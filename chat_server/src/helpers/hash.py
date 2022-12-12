from abc import abstractmethod
from passlib.context import CryptContext


class Hash:
    """Hash class to handle password crypting and verifing.
    """
    pwd_ctx = CryptContext(schemes="bcrypt", deprecated="auto")

    @classmethod
    def bcrypt(cls, password: str):
        """Returns hash of given password.
        """
        return cls.pwd_ctx.hash(password)

    @classmethod
    def verify(cls, hashed_password: str, plain_password: str):
        """Returns true if password and hashed password match.
        """
        return cls.pwd_ctx.verify(plain_password, hashed_password)
