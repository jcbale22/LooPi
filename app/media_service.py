import aioboto3
from app.config import R2_BUCKET_NAME, R2_ACCESS_KEY, R2_SECRET_KEY, R2_ENDPOINT_URL

session = aioboto3.Session()

async def upload_media_to_r2(file_obj, key):
    async with session.client(
        's3',
        region_name='auto',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY
    ) as client:
        await client.upload_fileobj(file_obj, R2_BUCKET_NAME, key)

async def generate_presigned_url(key, expires_in=3600):
    async with session.client(
        's3',
        region_name='auto',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY
    ) as client:
        return await client.generate_presigned_url(
            'get_object',
            Params={'Bucket': R2_BUCKET_NAME, 'Key': key},
            ExpiresIn=expires_in
        )
