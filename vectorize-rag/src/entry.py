from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint

EMBEDDING_MODEL = "@cf/baai/bge-base-en-v1.5"
GENERATION_MODEL = "@cf/openai/gpt-oss-120b"
DOCUMENTS = (
    {
        "id": "cloudflare-workers",
        "title": "Cloudflare Workers",
        "text": "Cloudflare Workers run JavaScript, TypeScript, and Python code close to users on Cloudflare's network.",
        "citation": "Cloudflare Workers overview",
    },
    {
        "id": "workers-ai",
        "title": "Workers AI",
        "text": "Workers AI provides model inference through an AI binding so a Worker can run supported models without managing inference servers.",
        "citation": "Workers AI overview",
    },
    {
        "id": "vectorize",
        "title": "Vectorize",
        "text": "Vectorize is Cloudflare's vector database for storing embeddings and retrieving similar vectors with semantic search.",
        "citation": "Vectorize overview",
    },
    {
        "id": "r2",
        "title": "R2",
        "text": "R2 is Cloudflare's S3-compatible object storage service for storing and retrieving objects without egress fees from Cloudflare.",
        "citation": "R2 overview",
    },
)


def json_response(payload, status=200, headers=None):
    return Response.json(payload, status=status, headers=headers)


def error_response(message, status, headers=None):
    return json_response({"error": message}, status, headers)


async def embed(ai, texts):
    result = await ai.run(EMBEDDING_MODEL, {"text": texts, "pooling": "cls"})
    return result.get("data")


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = urlparse(request.url).path

        match path:
            case "/":
                if request.method != "GET":
                    return error_response("Method not allowed.", 405, {"Allow": "GET"})

                return json_response(
                    {
                        "endpoints": {
                            "GET /": "overview",
                            "POST /seed": "seed corpus",
                            "POST /query": "query corpus",
                        },
                        "embedding_model": EMBEDDING_MODEL,
                        "generation_model": GENERATION_MODEL,
                        "setup": "Create python-rag-index, then POST /seed before POST /query.",
                    }
                )

            case "/seed":
                if request.method != "POST":
                    return error_response("Method not allowed.", 405, {"Allow": "POST"})

                return await self.seed()

            case "/query":
                if request.method != "POST":
                    return error_response("Method not allowed.", 405, {"Allow": "POST"})

                return await self.query(request)
            case _:
                return error_response("Not found.", 404)

    async def seed(self):
        """Seed the Vectorize index with documents."""
        vectors = await embed(self.env.AI, [document["text"] for document in DOCUMENTS])
        if not vectors:
            return error_response("Embedding response contained no data.", 502)

        records = [
            {
                "id": document["id"],
                "values": vector,
                "metadata": {
                    "title": document["title"],
                    "text": document["text"],
                    "citation": document["citation"],
                },
            }
            for document, vector in zip(DOCUMENTS, vectors)
        ]
        mutation = await self.env.VECTORIZE.upsert(records)
        return json_response(
            {
                "mutation_id": mutation["mutationId"],
                "document_count": len(DOCUMENTS),
                "status": "accepted; Vectorize writes propagate asynchronously, so retry /query shortly if no matches are visible yet.",
            },
            202,
        )

    async def query(self, request):
        """Query the Vectorize index with a question."""
        try:
            payload = await request.json()
        except ValueError:
            return error_response("Request body must be valid JSON.", 400)

        question = payload.get("question")
        if not isinstance(question, str) or not question.strip():
            return error_response("'question' must be a non-empty string.", 400)

        vectors = await embed(self.env.AI, [question.strip()])
        if not vectors:
            return error_response("Embedding response contained no data.", 502)
        result = await self.env.VECTORIZE.query(
            vectors[0], {"topK": 3, "returnMetadata": "all", "returnValues": False}
        )
        matches = []
        for match in result["matches"]:
            metadata = match.get("metadata")
            if not metadata or not metadata.get("text"):
                continue
            matches.append((match, metadata))
        if not matches:
            return error_response(
                "No indexed documents are visible yet. Seed first or retry shortly.",
                409,
            )

        sources = "\n\n".join(
            f"[{metadata.get('citation', match['id'])}] {metadata.get('title', 'Untitled')}: {metadata['text']}"
            for match, metadata in matches
        )
        prompt = (
            "Answer only from the supplied sources. If the sources do not answer the "
            "question, say so. Cite factual statements using the source labels exactly "
            f"as written.\n\nSources:\n{sources}\n\nQuestion: {question.strip()}"
        )
        generation = await self.env.AI.run(
            GENERATION_MODEL,
            {
                "messages": [
                    {
                        "role": "system",
                        "content": "You answer using only supplied sources and citations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 300,
            },
        )
        return json_response(
            {
                "answer": generation["choices"][0]["message"]["content"],
                "matches": [
                    {
                        "id": match["id"],
                        "citation": metadata.get("citation", match["id"]),
                        "title": metadata.get("title", "Untitled"),
                        "score": match["score"],
                    }
                    for match, metadata in matches
                ],
            }
        )
