from flask import Flask, jsonify, request
from workers import WorkerEntrypoint, wsgi


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await wsgi.fetch(app, request, self.env)


app = Flask(__name__)


@app.get("/")
def root():
    return jsonify(message="ok")


@app.get("/hello/<name>")
def hello(name):
    return jsonify(message=f"Hello, {name}!")


@app.post("/echo")
def echo():
    return jsonify(received=request.get_json(silent=True), args=request.args.to_dict())
