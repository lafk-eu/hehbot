import hehbot.gpt as gpt

async def get_embedding_async(text, model="text-embedding-3-small") -> list[float]:
    response = await gpt.async_client.embeddings.create(input=text, model=model)
    return response.data[0].embedding
