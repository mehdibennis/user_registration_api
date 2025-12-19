class DomainError(Exception):
    """Base class for domain exceptions"""

    pass


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email {email} already exists")


class UserNotFoundError(DomainError):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email {email} not found")


class InvalidActivationCodeError(DomainError):
    def __init__(self):
        super().__init__("Invalid activation code")


class ActivationCodeExpiredError(DomainError):
    def __init__(self):
        super().__init__("Activation code has expired")


class UserAlreadyActivatedError(DomainError):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User {email} is already active")
