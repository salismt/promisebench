"""Text of the emails we send to members. Keep them short and plain."""
from . import config

SIGNATURE = "\n\nThe Brightpath team\nQuestions? Call us on %s." % config.SUPPORT_PHONE


def welcome(name):
    return ("Welcome to Brightpath",
            "Hello %s,\n\nYour Brightpath account is ready. Sign in at %s with "
            "this email address and the password you chose.%s"
            % (name or "there", config.APP_URL, SIGNATURE))


def reset_link(name, token):
    url = "%s/reset-password?token=%s" % (config.APP_URL, token)
    minutes = config.RESET_TOKEN_TTL_SECONDS // 60
    return ("Reset your Brightpath password",
            "Hello %s,\n\nSomeone asked to reset the password for this account. "
            "If it was you, open this link within %d minutes:\n\n%s\n\n"
            "If it wasn't you, you can ignore this email.%s"
            % (name or "there", minutes, url, SIGNATURE))


def password_changed(name):
    return ("Your Brightpath password was changed",
            "Hello %s,\n\nThe password for your account was just changed. If you "
            "did not do this, call us straight away.%s" % (name or "there", SIGNATURE))


def locked_out(name, minutes):
    return ("Your Brightpath account is temporarily locked",
            "Hello %s,\n\nWe locked your account for %d minutes after several "
            "sign-in attempts with the wrong password. You can reset your password "
            "at %s/forgot-password.%s" % (name or "there", minutes, config.APP_URL, SIGNATURE))
