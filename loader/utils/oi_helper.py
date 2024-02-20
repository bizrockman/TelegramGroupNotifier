import openai


class OpenAIHelper:

    def __init__(self):
        self._openai_client = openai.OpenAI()

    def gpt_4v_raw_response(self, system_prompt, user_prompt, image_url):
        response = self._openai_client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "system", "content": f"{system_prompt}"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{user_prompt}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"{image_url}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=3000,
            temperature=0.7,
        )

        return response.choices[0]

    def gpt_4v_response(self, system_prompt, user_prompt, image_url):
        response = self.gpt_4v_raw_response(system_prompt, user_prompt, image_url)

        return response.message.content

    def gpt_4_raw_response(self, system_prompt, user_prompt):
        response = self._openai_client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {
                    "role": "system", "content": f"{system_prompt}",
                },
                {
                    "role": "user",
                    "content": f"{user_prompt}",
                }
            ],
            max_tokens=3000,
            temperature=0.7
        )

        return response.choices[0]

    def gpt_4_response(self, system_prompt, user_prompt):
        response = self.gpt_4_raw_response(system_prompt, user_prompt)

        return response.message.content

    def gpt_35_raw_response(self, system_prompt, user_prompt):
        response = self._openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", "content": f"{system_prompt}",
                },
                {
                    "role": "user",
                    "content": f"{user_prompt}",
                }
            ],
            max_tokens=3000,
            temperature=0.7
        )

        return response.choices[0]

    def gpt_35_response(self, system_prompt, user_prompt):
        response = self.gpt_4_raw_response(system_prompt, user_prompt)

        return response.message.content
