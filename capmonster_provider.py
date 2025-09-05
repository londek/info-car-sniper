from capmonster_python import CapmonsterClient, TurnstileTask

class CapmonsterProvider:
    def __init__(self, api_key: str):
        self.client = CapmonsterClient(api_key)

    def get_balance(self) -> float:
        return self.client.get_balance()

    def solve_turnstile(self, websiteUrl: str, websiteKey: str) -> str:
        task = TurnstileTask(
            websiteURL=websiteUrl,
            websiteKey=websiteKey
        )

        task_id = self.client.create_task(task)
        result = self.client.join_task_result(task_id)

        return result["token"]