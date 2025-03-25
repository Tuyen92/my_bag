class OTPException(BaseException):
    pass


class OTPEmailNotExists(OTPException):
    pass


class NeedToRequestNewOTP(OTPException):
    pass


class OTPExpiredOrIncorrect(OTPException):
    pass


class OTPEmailUpdateFailed(OTPException):
    pass


class OTPEmailCreateFailed(OTPException):
    pass
