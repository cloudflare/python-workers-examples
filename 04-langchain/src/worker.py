from workers import handler, Response
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI


@handler
async def on_fetch(request, env):
    prompt = PromptTemplate.from_template(
        "Complete the following sentence: I am a {profession} and "
    )
    llm = OpenAI(api_key=env.API_KEY)
    chain = prompt | llm

    res = await chain.ainvoke({"profession": "electrician"})
    return Response(res.split(".")[0].strip())
