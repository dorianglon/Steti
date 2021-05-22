from twilio.rest import Client


class NotificationSMS:

    def __init__(self):
        self.account_sid = 'AC7fa8357a4bfd17d05615ae565172632f'
        self.auth_token = '624a94e55bed49115b1fdde42a67efe7'
        self.client = Client(self.account_sid, self.auth_token)
        self.send_from = '+16193637293'

    def send_client_sms(self, clients):
        for number in clients:
            self.client.messages.create(
                body='New Notification from Steti Technologies.\nA new post has been flagged.',
                from_=self.send_from,
                to=number
            )

    def send_admin_ms(self, admins):
        for number in admins:
            self.client.messages.create(
                body="New PDF ready for upload.",
                from_=self.send_from,
                to=number
            )
