from datetime import UTC, datetime

import pg8000
from constants import FLUSH_DELAY, PENDING_KEY, REACTIONS, ROOM_KEY, TOTALS_KEY
from workers import DurableObject


class ReactionRoom(DurableObject):
    """
    A Durable Object that tracks reaction counts for a chat room.

    Methods:
        add_reaction: Add a reaction to the room
        get_stats: Get the current stats for the room
    """

    def __init__(self, state, env):
        super().__init__(state, env)
        self.env = env
        # pending: reactions that have not been flushed to the database yet
        self.pending: dict[str, int] = dict.fromkeys(REACTIONS, 0)
        # totals: total reactions for the room
        self.totals: dict[str, int] = dict.fromkeys(REACTIONS, 0)
        self.room_id = None
        self.loaded = False

        self.ctx.blockConcurrencyWhile(self._load_pending)

    async def add_reaction(self, room_id, reaction):
        if self.room_id is not None and self.room_id != room_id:
            raise ValueError("Room ID does not match this Durable Object")

        next_pending = self.pending.copy()
        next_totals = self.totals.copy()
        next_pending[reaction] += 1
        next_totals[reaction] += 1
        self.room_id = room_id
        self.pending = next_pending
        self.totals = next_totals

        await self._schedule_alarm_if_needed()
        await self._save_state(room_id, next_pending, next_totals)

        return {
            "accepted": reaction,
            "totals": self.totals.copy(),
            "pending": self.pending.copy(),
        }

    async def get_stats(self, room_id):
        persisted = dict.fromkeys(REACTIONS, 0)
        connection = None
        try:
            connection = self._connection()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT reaction, count FROM reaction_stats WHERE room_id = %s",
                (room_id,),
            )
            for reaction, count in cursor.fetchall():
                persisted[reaction] = int(count)
        finally:
            if connection is not None:
                connection.close()
        return {
            "totals": self.totals.copy(),
            "persisted": persisted,
            "pending": self.pending.copy(),
        }

    async def _load_pending(self):
        """
        If the durable object is removed and recreated, the state will be lost.
        Load the data from persistent storage.
        """
        if self.loaded:
            return

        stored = await self.ctx.storage.get([PENDING_KEY, TOTALS_KEY, ROOM_KEY])
        pending = stored.get(PENDING_KEY)
        totals = stored.get(TOTALS_KEY)
        if pending:
            self.pending = {
                reaction: int(pending.get(reaction, 0)) for reaction in REACTIONS
            }
        if totals:
            self.totals = {
                reaction: int(totals.get(reaction, 0)) for reaction in REACTIONS
            }
        self.room_id = stored.get(ROOM_KEY)
        self.loaded = True

    async def _save_state(self, room_id, pending, totals):
        await self.ctx.storage.put(
            {
                ROOM_KEY: room_id,
                PENDING_KEY: pending,
                TOTALS_KEY: totals,
            }
        )

    async def _schedule_alarm_if_needed(self):
        if await self.ctx.storage.getAlarm() is None:
            await self.ctx.storage.setAlarm(datetime.now(UTC) + FLUSH_DELAY)

    async def _schedule_retry(self):
        await self.ctx.storage.setAlarm(datetime.now(UTC) + FLUSH_DELAY)

    def _connection(self):
        hd = self.env.HYPERDRIVE
        return pg8000.connect(
            host=hd.host,
            port=int(hd.port),
            user=hd.user,
            password=hd.password,
            database=hd.database,
            ssl_context=False,
        )

    async def alarm(self, alarm_info):
        # Block concurrency while flushing to prevent race conditions
        self.ctx.blockConcurrencyWhile(self._flush)

    async def _flush(self):
        batch = self.pending.copy()
        if not any(batch.values()):
            return
        totals = self.totals.copy()

        connection = None
        try:
            connection = self._connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO reaction_stats (room_id, reaction, count)
                VALUES (%s, %s, %s), (%s, %s, %s), (%s, %s, %s)
                ON CONFLICT (room_id, reaction) DO UPDATE SET
                    count = EXCLUDED.count,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    self.room_id,
                    "heart",
                    totals["heart"],
                    self.room_id,
                    "laugh",
                    totals["laugh"],
                    self.room_id,
                    "fire",
                    totals["fire"],
                ),
            )
            connection.commit()
        except Exception as error:
            if connection is not None:
                try:
                    connection.rollback()
                except Exception as rollback_error:
                    print(f"Reaction rollback failed: {rollback_error}")
            print(f"Reaction flush failed: {error}")
            await self._schedule_retry()
            return
        finally:
            if connection is not None:
                connection.close()

        next_pending = {
            reaction: self.pending[reaction] - count
            for reaction, count in batch.items()
        }
        await self._save_state(self.room_id, next_pending, self.totals)
        self.pending = next_pending
        if any(self.pending.values()):
            await self._schedule_alarm_if_needed()
