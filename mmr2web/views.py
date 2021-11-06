from django.shortcuts import render

import django.utils
from django.shortcuts import render_to_response
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.urls import reverse
from django.db import transaction
from mmr2web.models import *
#from mmr2web.forms import *
from django.db.models import Sum
import datetime
import re
import sys
from django.utils.translation import gettext as _
from django.conf import settings
from django.utils import translation

# Create your views here.
def login(request):
    user_language = 'en'
    translation.activate(user_language)
    response = HttpResponse()
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
    if finished():
        return render_to_response('done.html')
    psid = extract_psid(request)
    if not psid:
        return render_to_response('login_failed.html')
    try:
        p = get_player(psid)
        assert p
    except:
        try:
            assert valid_psid(psid)
            p = Player(psid=psid)
            p.save()
            return HttpResponseRedirect(p.continue_url(reverse(consent)))
        except:
            return render_to_response('login_failed.html')
    p = get_player(psid)
    if p.status == 10:
        if finished():
            return render_to_response('done.html')
        return HttpResponseRedirect(p.continue_url(reverse(consent)))
    elif p.status == 20:
        return HttpResponseRedirect(p.continue_url(reverse(instructions)))
    elif p.status == 30:
        return HttpResponseRedirect(p.continue_url(reverse(decision)))
    elif p.status == 40:
        return HttpResponseRedirect(p.continue_url(reverse(question)))
    elif p.status == 50:
        return HttpResponseRedirect(p.continue_url(reverse(feedback)))
    elif p.status == 110:
        return HttpResponseRedirect(p.exit_url())
    elif p.status == 100:
        return HttpResponseRedirect(player.no_consent())
    else:
        return render_to_response('login_failed.html')

def consent(request):
    if finished():
        return render_to_response('done.html')
    psid = extract_psid(request)
    if not psid:
        return render_to_response('login_failed.html')
    player = get_player(psid)
    if request.method=='POST':
        try:
            if request.POST['consent']=="Yes":
                player.consent = True
                draw_dice(player)
                # Generate questions
                for qtype in NQD.keys():
                    order, template = NQD[qtype]
                    q = Noincentivequestion(player=player,
                                                qtype=qtype,
                                                order=order)
                    q.save()
                player.status = 20
                player.save()
                return HttpResponseRedirect(player.continue_url(reverse(instructions)))
            elif request.POST['consent']=="No":
                player.consent = False
                player.status = 100
                player.save()
                return HttpResponseRedirect(player.no_consent())
        except:
            pass
    context = {'psid': psid}
    return render_to_response('consent.html', context)

def instructions(request):
    if finished():
        return render_to_response('done.html')
    psid = extract_psid(request)
    if not psid:
        return render_to_response('login_failed.html')
    player = get_player(psid)
    if player.status != 20:
        return HttpResponseRedirect(player.continue_url(reverse(login)))       
    context = {'psid': psid, 'ndice': NDICE,
               'now': player.treatment=='now',
               'week': player.treatment=='week',
               'month': player.treatment=='month',
               'never': player.treatment=='never'}
    
    if request.method=='POST':
        try:
            if request.POST['instructions1']=="Yes":
                return render_to_response('instructions2.html', context)
        except:
            pass
        try:
            if request.POST['instructions2']=="Yes":
                player.status = 30
                player.save()
                return HttpResponseRedirect(player.continue_url(reverse(decision)))
        except:
            pass
    return render_to_response('instructions1.html', context)

def decision(request):
    if finished():
        return render_to_response('done.html')
    psid = extract_psid(request)
    if not psid:
        render_to_response('login_failed.html')
    player = get_player(psid)
    if player.status != 30:
        return HttpResponseRedirect(player.continue_url(reverse(login)))    
    die = get_first_active_die(player)
    if not die: # All decisions have been made
        player.status = 40
        player.save()
        return HttpResponseRedirect(player.continue_url(reverse(question)))
    situations = list( Situation.objects.filter(player=player, die = die).order_by('row') )
    nchoice = len(situations)
    error = ""
    dice = [ {'sitnr': x.row, 'name': "sit%d" % x.row, 'safe': x.safe_amount } for x in situations  ]

    context = {'psid': psid,
               'color': die.color.lower(),
               'nchoice': nchoice,
               'dicefaces': DICE[die.dienumber]['eyes'],
               'farge': _(DICE_TRANSLATION[die.color]),
               'farg': _(DICE_TRANSLATION_E[die.color]),
               'dice': dice,
               'error': "",
               'now': player.treatment=='now',
               'week': player.treatment=='week',
               'month': player.treatment=='month',
               'never': player.treatment=='never',
               }
    if request.method == 'POST':
        try: 
            for d in dice:
                rchoice = (request.POST[d['name']] == 'risk')
                sit = Situation.objects.get(player=player, die=die, row=(d['sitnr']) )
                sit.choice_risk = rchoice
                sit.save()
            die.active = False
            die.save()
            return HttpResponseRedirect(player.continue_url(reverse(decision)))
        except:
            context['error'] = _("""<p style="color:red"> Du må gjøre et valg i alle de %d situasjonene for å kunne gå videre.</p>""")  % nchoice
    return render(request, 'choice.html', context)
    
    

def question(request):
    if finished():
        return render_to_response('done.html')
    psid = extract_psid(request)
    if not psid:
        render_to_response('login_failed.html')
    player = get_player(psid)
    if player.status != 40:
        return HttpResponseRedirect(player.continue_url(reverse(login)))
    q = get_firstactive_noincentivequestion(player)
    if not q:   # The participant finished all questions, so a valid 
        draw_payment(player)        
        player.status = 50
        player.save()
        return HttpResponseRedirect(player.continue_url(reverse(feedback)))
    error = ""
    if request.method == 'POST' and request.POST['qtype']==q.qtype:
        try:
            itemstring = request.POST['items']
            items = itemstring.split(',')
            output = []
            qtype = request.POST['qtype']
            for item in items:
                choice = request.POST[item]
                output.append( (item, choice))
            # If I got all the way here, it must mean that I could unpack all valid values.
            # I can then attempt to input those values to the database.
            for item, choice in output:
                answ = Noincentiveanswer(player=player,
                                         question=q,
                                         item = item,
                                         answer=choice)
                answ.save()
            q.active=False
            q.save()
            return HttpResponseRedirect(player.continue_url(reverse(question)))
        except:
            error = _("""<p style="color:red"> Du må svare på spørsmålene.</p>""")
    q = get_firstactive_noincentivequestion(player)
    if not q:
        draw_payment(player)        
        player.status = 50
        player.save()
        return HttpResponseRedirect(player.continue_url(reverse(feedback)))
    order, temp = NQD[q.qtype]
    context = {'error': error ,
               'psid': psid}
    return render(request, temp, context)

def feedback(request):
    if finished():
        return render_to_response('done.html')
    psid = extract_psid(request)
    if not psid:
        render_to_response('login_failed.html')
    player = get_player(psid)
    if player.status != 50:
        return HttpResponseRedirect(player.continue_url(reverse(login)))    
    context = {'psid': psid }               
    if request.method=='POST':
        try:
            if request.POST['feedback']=="Yes":
                player.status = 110 
                player.save()
                return HttpResponseRedirect(player.exit_url())
        except:
            pass
    if player.treatment == 'week':
        message = _("Du vil bli kontaktet av Norstat om en uke med utfallet for mottakeren.")
    elif player.treatment == 'month':
        message = _("Du vil bli kontaktet av Norstat om tre måneder med utfallet for mottakeren.")
    elif player.treatment == 'never':
        message = _("Du vil ikke få beskjed om utfallet for mottakeren.")
    else:
        fd = FinalDraws.objects.get(player=player)
        message = fd.message
    context['message'] = message
    return render_to_response('message.html', context)    
