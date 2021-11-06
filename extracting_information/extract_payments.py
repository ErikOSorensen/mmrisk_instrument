from mmr2web.models import *
import datetime


def get_payments_file(nok_per_usd=9.1412):
    """Default exchange rate taken from Norges Bank, Nov 22, 2019."""
    payments_out = open("payments_mmrisk.csv", "w")
    payments_out.write("amount,message\n")
    total_payment = 0
    for s in Situation.objects.filter(selected=True):
        if s.choice_risk:
            amount = DICE[s.die.dienumber]['eyes'][s.draw-1] / nok_per_usd
            message = "In mmr2 - someone decided to throw a dice on your behalf."
            if amount==0:
                amount=0.01
                message = "In mmr - someone decided to throw a dice on your behalf and you were unlucky."
        else:
            amount = s.safe_amount / nok_per_usd
            message = "In mmr2 - someone decided for the safe amount on your behalf."
        payments_out.write("%3.2f,%s\n" % (amount, message))
        total_payment += amount
    payments_out.close()
    return total_payment

get_payments_file()
