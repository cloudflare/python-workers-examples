from langchain_cloudflare import ChatCloudflareWorkersAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        prompt = PromptTemplate.from_template(
            "In one sentence, describe a great day in the life of an {profession}."
        )
        llm = ChatCloudflareWorkersAI(
            model_name="@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            binding=self.env.AI,
            max_tokens=64,
        )
        chain = prompt | llm | StrOutputParser()

        result = await chain.ainvoke({"profession": "electrician"})
        return Response.json({"result": result})
