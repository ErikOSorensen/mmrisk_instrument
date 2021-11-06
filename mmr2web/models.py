from django.db import models
import random, string
from django.db.models.deletion import SET_NULL, CASCADE
from django.urls import reverse
import datetime
from django.utils.translation import gettext as _

BASE_URL = "https://localhost/projects/end"

NDICE = 4
TREATMENTS = ('now', 'week', 'month', 'never',)
P_BINDING = 0.2
DICE_COLORS = ('RED', 'YELLOW', 'GREEN', 'BLUE',)
DICE_TRANSLATION = {'RED': _('røde'), 'YELLOW': _('gule'), 'GREEN': _('grønne'), 'BLUE': _('blå')}
DICE_TRANSLATION_E = {'RED': _('rød'), 'YELLOW': _('gul'), 'GREEN': _('grønn'), 'BLUE': _('blå')}

DICE = ( { 'i':0,  'eyes': (0,0,0,0,0,240), 'safe': (10,20,30,40,50,60,70) },
         { 'i':1,  'eyes': (0,0,0,0,240,240), 'safe': (20,40,60,80,100,120,140) },
         { 'i':2,  'eyes': (0,0,0,0,120,120), 'safe': (10,20,30,40,50,60,70) },
         { 'i':3,  'eyes': (120,120,120,120,240,240), 'safe': (130,140,150,160,170,180,190) },
         { 'i':4,  'eyes': (60,60,60,60,120,120), 'safe': (70,75,80,85,90,95,100)}, 
         { 'i':5,  'eyes': (80,80,80,80,200,200), 'safe': (90,100,110,120,130,140,150)},
         { 'i':6,  'eyes': (180,180,180,180,240,240), 'safe': (190,195,200,205,210,215,220)},
         { 'i':7,  'eyes': (0,0,0,240,240,240), 'safe': (30,70,100,130,170,200,230)},
         { 'i':8,  'eyes': (0,0,240,240,240,240), 'safe': (30,70,100,130,170,200,230)},
         { 'i':9,  'eyes': (0,240,240,240,240,240), 'safe': (30,70,100,130,170,200,230)},
         )

NQD = { 'q1': (1, 'q1.html'),
        'q2': (2, 'q2.html'),
        'q3': (3, 'q3.html'),
        'q4': (4, 'q4.html'),
        'qbackground': (5, 'qbackground.html')
        }

class Player(models.Model):
    psid = models.CharField(max_length=80, unique=True)
    treatment = models.CharField(max_length=10)
    status = models.IntegerField(default=10)
    consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def continue_url(self, urlbase):
        url = urlbase + "?psid=%s" % self.psid
        return url
    def exit_url(self):
        url = "https://norstatsurveys.com/wix/p1875224158.aspx?status=complete"
        return url
    def no_consent(self):
        url = "https://norstatsurveys.com/wix/p1875224158.aspx?status=screened"
        return url
    
class Die(models.Model):
    player = models.ForeignKey(Player, on_delete=CASCADE)
    dienumber = models.IntegerField()                   # index into DICE
    i = models.IntegerField()
    n = models.IntegerField()
    active=models.BooleanField(default=True)
    color = models.CharField(max_length=10)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('player', 'color')
    
class Situation(models.Model):
    player = models.ForeignKey(Player, on_delete=CASCADE)
    die = models.ForeignKey(Die, on_delete=CASCADE)
    safe_amount = models.IntegerField()
    row = models.IntegerField()
    choice_risk = models.BooleanField(null=True)
    selected = models.BooleanField(default=False)
    draw = models.IntegerField(null=True)

class FinalDraws(models.Model):
    player = models.ForeignKey(Player, on_delete=CASCADE)
    message = models.CharField(max_length=160)
    message_date = models.DateField(null=True)

class Noincentivequestion(models.Model):
    player = models.ForeignKey(Player, on_delete=CASCADE)
    active=models.BooleanField(default=True)
    order = models.IntegerField()
    qtype = models.CharField(max_length=20)

class Noincentiveanswer(models.Model):
    player = models.ForeignKey(Player, on_delete=CASCADE)
    question = models.ForeignKey(Noincentivequestion, on_delete=CASCADE)
    item= models.CharField(max_length=20)
    answer = models.CharField(max_length=240)

def get_player(psid):
    try:
        return Player.objects.get(psid=psid)
    except:
        return False

def get_firstactive_noincentivequestion(player):
    try:
        return Noincentivequestion.objects.filter(player=player, active=True).order_by('order')[0]
    except:
        return False

def get_first_active_die(player):
    try:
        return Die.objects.filter(player=player, active=True).order_by('i')[0]
    except:
        return False

def randomstring(n):
    chars = string.letters.upper()
    x = ""
    for s in range(n):
        x = x + random.choice(chars)
    return x

def extract_psid(request):
    if request.method == 'GET':
        try:
            psid = request.GET['psid']
        except:
            psid = False
    elif request.method == 'POST':
        try:
            psid = request.POST['psid']
        except:
            psid = False
    return psid
   
def draw_dice(player):
    player.treatment = random.choice(TREATMENTS)
    dice = random.sample(DICE,NDICE)
    k = random.randint(0, len(DICE_COLORS))
    for j, die in enumerate(dice):
        cindex = ( j+k ) % ( len(DICE_COLORS) ) 
        color = _(DICE_COLORS[ cindex ])
        d = Die(player=player,
                dienumber=die['i'],
                i = j+1,
                n = NDICE,
                color = color)
        d.save()
        for l, amount in enumerate(DICE[d.dienumber]['safe']):
            s = Situation(player = player,
                          die = d,
                          safe_amount = amount,
                          row = l+1)
            s.save()
    player.save()

def draw_payment(player):
    u = random.uniform(0,1)
    if u < P_BINDING: # Payment will be made
        all_sits = list( Situation.objects.filter(player=player) )
        selected_sit = random.choice(all_sits)
        selected_sit.selected = True
        selected_sit.draw = random.randint(1,6)        # Lottery drawn 
        selected_sit.save()
        die_drawn = DICE[ selected_sit.die.dienumber ]
        color = selected_sit.die.color
        if not selected_sit.choice_risk:
            message = _("Du valgte det sikre utfallet med den %s terningen i situasjon %d, mottakeren får %d kr.") % (DICE_TRANSLATION[color], 
                                                                                                                    selected_sit.row, 
                                                                                                                    selected_sit.safe_amount)
        else:
            message = _("Du valgte den %s terningen, terningen viste %d, mottakeren får %d kr.") % (DICE_TRANSLATION[color],
                                                                                                 selected_sit.draw,
                                                                                                 die_drawn['eyes'][selected_sit.draw-1])     
    else:
        if player.treatment != 'never':
            message = _("Ingen av dine beslutninger ble trukket til å bestemme utbetaling.")
    if player.treatment == 'never':
        message = _("Du vil ikke få beskjed om utfallet for mottakeren.")
    if player.treatment=='now':
        mdate = datetime.date.today()
    elif player.treatment=='week':
        mdate = datetime.date.today() + datetime.timedelta(7)
    elif player.treatment=='month':
        mdate = datetime.date.today() + datetime.timedelta(90)
    else:
        mdate = None
    fd = FinalDraws( player = player,
                     message = message,
                     message_date = mdate )
    fd.save()

def valid_psid(psid):
    try:
        ipsid = int(psid)
    except:
        return False
    return  ( ( (ipsid - 7) % 13)  == 0)

def finished():
    n = Player.objects.filter(status__in=[50,110]).count()
    return (n>=2000)

