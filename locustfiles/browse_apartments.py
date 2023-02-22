import random
from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task(15)
    def view_apartments(self):
        self.client.get("/apartment/", name="/apartment/")
        # print(self.result)

    @task(14)
    def view_apartment(self):
        apartment_id = random.randrange(1, 15)
        self.client.get(f"/apartment/{apartment_id}/", name="/apartment/:id/")

    # @task(5)
    def create_apartments(self):
        # django.setup()
        self.client.post(
            "/apartment/",
            name="/apartment/create/",
            json={
                "title": "string",
                "category": "Bungalow",
                "price": random.randint(250, 400),
                "locality": "string",
                "state": "string",
                "area": "string",
                "street": "string",
                "specifications": {
                    "additionalProp1": "string",
                    "additionalProp2": "string",
                    "additionalProp3": "string",
                },
                "descriptions": "string",
                "is_available": True,
            },
            headers={
                'Authorization': f'JWT {random.choice(self.access_tokens)}'
            }
        )

    # @task(10)
    def login(self):
        resp = self.client.post('/accounts/login/', json={'email':f'testuser{random.randint(1,3)}@gmail.com', 'password':'@Huzkid619'}, name = '/login/additional/')
        self.access_tokens.append(resp.json()['access_token'])
    
    # @task(5)
    def make_booking(self):
        self.client.post("/bookmark/", json={"apartment_id": 1}, headers={
                'Authorization': f'JWT {random.choice(self.access_tokens)}'
            })

    # def on_start(self):
    #     # First log in all the agents so they can create apartments

    #     self.access_tokens = list()

    #     resp = self.client.post('/accounts/login/', json={'email':'admin@django.com', 'password':123}, name = '/login/')
    #     self.access_tokens.append(resp.json()['access_token'])
    #     # self.access_tokens.append(resp.json()['access_token'])
