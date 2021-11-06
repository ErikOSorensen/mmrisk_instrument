from mmr2web.models import *
import datetime

def feedback_file():
  feedback_out = open("feedback_mmr2.csv", "w")
  feedback_out.write("psid;message;message_date\n")
  for fd in FinalDraws.objects.all():
    if fd.player.treatment in ('week', 'month'):
      dtstring = fd.player.created_at.strftime("%Y-%m-%d")
      feedback_out.write("%s;%s (Ref Norstat-undersøkelse %s);%s\n" % (fd.player.psid,fd.message,dtstring,fd.message_date))
  feedback_out.close()










def get_players_file():
  players_out = open("players.csv", "w")
  players_out.write("psid,treatment,status,created_at\n")
  for p in Player.objects.all():
    players_out.write("%s,%s,%d,%s\n" % (p.psid,
                                       p.treatment,
                                       p.status,
                                       p.created_at))
  players_out.close()
  

def get_decisions_file():
  decisions_out = open("decisions.csv", "w")
  decisions_out.write("psid,dienumber,safe_amount,choice_risk,updated_at\n")
  for s in Situation.objects.all():
    if s.die.active:
      continue
    decisions_out.write("%s,%d,%d,%d,%s\n" % (s.player.psid,
                                           s.die.dienumber,
                                           s.safe_amount,
                                           s.choice_risk,
                                           s.die.updated_at))
  decisions_out.close()
  

def get_answers():
  answers_out = open("answers.csv", "w")
  answers_out.write("psid,item,answer\n")
  for a in Noincentiveanswer.objects.all():
    answers_out.write("%s,%s,%s\n" % (a.player.psid,
                                      a.item,
                                      a.answer))
  answers_out.close()
  
def get_data():
  get_players_file()
  get_decisions_file()
  get_answers()

