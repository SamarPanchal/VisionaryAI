import requests as rq
import time
import io

API_KEY = '62dc81be0e21e3da248d16c87f01890e7cf879ce9cb1e5d089a7fdc4548cef6c7924dfaece0c1bb4d1d0972ca309b7f5'


def error(message):
    print(f"Error: <-- {message} -->")


def verified():
    verify = input("Please make sure you have typed your prompt correctly (y/n) : ")
    if verify.casefold() == 'y':
        return True
    else:
        return False


def request_image(prompt, extra):
    try:
        r = rq.post('https://clipdrop-api.co/text-to-image/v1',
                    files={
                        'prompt': (None, prompt + f" - effect ({extra})", 'text/plain')
                    },
                    headers={'x-api-key': API_KEY}
                    )
        if r.ok:
            return io.BytesIO(r.content)
        else:
            return False
    except Exception as e:
        return e


# if __name__ == '__main__':
#     print("<--- Welcome to Mac9 AI - Text to Image Generator (Beta) --->")

#     while True:
#         user_prompt = input("Please Describe your Image: ")
#         if user_prompt.isdigit():
#             error("Invalid Prompt!")
#         elif len(user_prompt) > 1000:
#             error("You have reached the maximum number of characters!")
#         else:
#             if verified():
#                 image_stream = request_image()
#                 if image_stream:
#                     image = Image.open(image_stream)
#                     index = time.strftime("%H:%M:%S__%Y-%m-%d)")
#                     image.save(f'{index}.png')
#                     print(f" <-- SUCCESS --- Image generated successfully and saved as '{index}'. ---> ")
