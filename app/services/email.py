from app.services.email_strategy import Emailstrategy


def send_class_reminder(
    member_email: str,
    member_name: str,
    class_info: dict,
) -> tuple[bool, str]:
    """ Goes directly to email strategy """
    strategy = Emailstrategy()
    return strategy.send_reminder(member_email, member_name, class_info)
