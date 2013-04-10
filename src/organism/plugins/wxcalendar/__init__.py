# Organism - A highly modular and extensible outliner.
# Copyright (C) 2011-2013 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of Organism.
#
# Organism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Organism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Organism.  If not, see <http://www.gnu.org/licenses/>.

import wx
import time as _time
import random  # *****************************************************************

from organism.coreaux_api import log
import organism.core_api as core_api
import organism.extensions.organizer_api as organizer_api

# Mozilla Lightning sembra usare 900 *********************************************
_CAL_RES = 900
# Adattare all'altezza di una riga di testo? *************************************
_ROW_HEIGHT = 16
_CELL_BORDER = 1
# Questo path va reso dinamico!!! ************************************************
_CANVAS = 'src/plugins/wxcalendar/canvas.png'


class Calendar(wx.ScrolledWindow):
    box = None
    timebox = None
    occpanel = None
    occgrid = None
    bground = None
    
    def __init__(self, parent):
        # Vedere wxWebkit http://wxwebkit.kosoftworks.com/ ***********************
        # Vedere http://code.google.com/p/wxscheduler/ ***************************
        # Come trattare le occorrenze senza data di fine? (durata nulla) *********
        #     si potrebbe dare una durata fittizia di 1 minuto
        # Come trattare le occorrenze che spannano su piu' giorni? ad esempio ****
        #     e' una cosa probabile per le occorrenze che iniziano vicino a
        #     mezzanotte
        # Per i task "accavallati" vedere se il grid sizer e' in grado di ********
        #     mantenere le colonne dei giorni della stessa lunghezza, e quindi
        #     strettire i task al bisogno
        # Permettere di "nascondere" una parte della giornata (ad esempio la *****
        #     notte)
        #   oppure scrollare automaticamente ad un'ora predefinita
        # Possibile algoritmo: ***************************************************
        #   * inizializzare maxcolumns a 1
        #   * creare un dizionario con, come chiavi, il numero di ogni riga del
        #     giorno (o un'analoga lista usando i suoi indici): creare 1440/min
        #     righe, dove min e' la risoluzione della griglia, cioe' l'altezza
        #     di una riga in minuti
        #   * ad ogni riga associare una lista di tutte le occorrenze che
        #     rientrano in quella specifica riga
        #   * contemporaneamente creare le liste 'conflicts' del dizionario di
        #     cui sotto; inoltre in quel dizionario impostare 'w' all'inverso
        #     del numero massimo di elementi tra le righe in cui appare l'item
        #     corrente, a rappresentare la frazione di larghezza da occupare;
        #     se width > maxcolumns, impostare maxcolumns a width
        #   * ottenere un dizionario cosi' fatto:
        #     {id_1: {'w': width, 'x1': lside, 'x2': rside,
        #                                      'conflicts': [id_4, id_7, ...]},
        #      id_2: {...},
        #      ...
        #      id_4: {..., 'conflicts': [id_1, id_7, ...]},
        #      ...
        #      id_17: {...},
        #     }
        #     come lside impostare a 0, cioe' inizializzo l'ascissa
        #     del lato sinistro combaciante col bordo sinistro della colonna
        #     del giorno; come rside impostare a 1, cioe' inizializzo l'ascissa
        #     del lato destro combaciante col bordo destro della colonna del
        #     giorno
        #   * per ogni id_ del dizionario risolvere i conflitti in questo modo:
        #     * se tutti gli 'x2' delle item in 'conflicts' sono == 1 (cioe'
        #       tutte le item arrivano al bordo destro della colonna del
        #       giorno) allora lascia l''x1' dell'item corrente a 0
        #       e imposta il suo 'x2' a 'x1' + 'w';
        #     * se invece in 'conflicts' ci sono items con 'x2' < 1, trovare il
        #       massimo tra gli 'x2' < 1 e impostare l''x1' dell'item corrente
        #       a questo valore, impostare il suo 'x2' a 'x1 + 'w' e cancellare
        #       da conflicts tutte le item con 'x2' < 1; inoltre, per ognuna di
        #       queste item, cancellare l'item corrente nel 'conflicts' della
        #       propria voce nel dizionario, dato che il conflitto e' stato
        #       appena risolto
        #     * ripetere questo sotto-ciclo finche' non ci sono piu' conflitti
        #   * a questo punto dovrei poter disegnare la colonna con un
        #     GridBagSizer, usando maxcolumns come numero di colonne
        # Possibile algoritmo (vecchia idea): ************************************
        #   * creare un dizionario con delle 2-tuple come chiavi che
        #     rappresentino le coordinate di una griglia: creare 1440/min,
        #     dove min e' la risoluzione della griglia, cioe' l'altezza di
        #     una riga in minuti; al momento creare solo la colonna 0
        #   * per ogni chiave del dizionario mettere una lista di tutte le
        #     occorrenze che rientrano in quella specifica riga
        #   * contemporaneamente creare un dizionario inverso in cui ad ogni
        #     occorrenza associo la lista di tutte le "celle" in cui e'
        #     presente del dizionario di cui sopra
        #   * se almeno una riga del primo dizionario ha piu' di un'occorrenza
        #     associata, ripeto il ciclo creando una nuova colonna nel
        #     dizionario, in cui, per ogni riga, se c'e' una sola occorrenza
        #     la "espando" nella colonna successiva, altrimenti lascio la prima
        #     occorrenza nella prima colonna e porto tutte le altre nella
        #     seconda colonna; contemporaneamente a questo aggiorno anche il
        #     secondo dizionario, notando che devo verificare, e nel caso
        #     assicurare, che ogni occorrenza occupi un "rettangolo" di "celle"
        #   * ripeto il ciclo delle "espansioni" finche' ogni "cella" del primo
        #     dizionario ha 0 o 1 occorrenze
        #   * a questo punto dovrei poter disegnare la colonna con un
        #     GridBagSizer basandomi sul secondo dizionario
        #   Notare che questo metodo genera divisioni asimmetriche, infatti se
        #     c'e' una riga con 2 occorrenze, ed un'altra con 5, la prima viene
        #     divisa in 1 e 4 colonne, e la seconda in 1, 1, 1, 1 e 1 colonne.
        wx.ScrolledWindow.__init__(self, parent)
        self.SetScrollRate(20, 20)
        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.box)
        
        self._init_timebox()
        self._init_occurrences()
    
    def _init_timebox(self):
        self.timebox = wx.BoxSizer(wx.VERTICAL)
        self.box.Add(self.timebox)
        
        resolution = _CAL_RES
        row_height = _ROW_HEIGHT
        cell_border = _CELL_BORDER
        
        for t in range(24):
            h = (3600 // resolution) * (row_height + cell_border * 2)
            label = wx.StaticText(self, label=''.join((str(t), ':00')),
                                  size=(-1, h))
            self.timebox.Add(label, flag=wx.ALIGN_RIGHT | wx.LEFT |
                             wx.RIGHT, border=4)
    
    def _init_occurrences(self):
        # Non riesco a togliere il bordo nero!!! *********************************
        #   al momento ho risolto con un offset di DrawRectangle in
        #     make_bground()
        self.occpanel = wx.Panel(self, style=wx.BORDER_NONE)
        self.box.Add(self.occpanel, 1, flag=wx.EXPAND)
        
        # Do not put cell gap here because it messes things up
        self.occgrid = wx.GridBagSizer()
        self.occpanel.SetSizer(self.occgrid)
        self.occgrid.SetEmptyCellSize((-1, _ROW_HEIGHT + _CELL_BORDER * 2))
        
        # Se riuscissi a creare l'immagine dinamicamente sarei a cavallo *********
        self.bground = wx.Bitmap(_CANVAS)
        self.refresh_bground()
        
        self.occpanel.Bind(wx.EVT_SIZE, self.refresh_bground)
        self.Bind(wx.EVT_SCROLLWIN, self.refresh_bground)
    
    def refresh_bground(self, event=None):
        wx.FutureCall(50, self.make_bground)
        # This method is called also explicitly
        if event:
            event.Skip()
        
    def make_bground(self):
        # Questo metodo devo studiarlo meglio ************************************
        #     fonte: http://www.daniweb.com/software-development/python/threads/128350/1119379#post1119379
        # BUG: le dialog box azzerano il background!!! ***************************
        dc = wx.ClientDC(self.occpanel)
        # Se riuscissi a creare l'immagine dinamicamente sarei a cavallo *********
        brush_bmp = wx.BrushFromBitmap(self.bground)
        dc.SetBrush(brush_bmp)
        w, h = self.occpanel.GetClientSize()
        # wx.DC ha tanti altri metodi di disegno interessanti! *******************
        # Al momento uso un offset di 1 px per mascherare il border del Panel ****
        dc.DrawRectangle(-1, -1, w + 2, h + 2)
        
    def refresh(self):
        # Questa funzione e' troppo lenta, va threadata **************************
        #     inoltre sarebbe bene testarla con microtime e provare ad
        #     ottimizzarla
        #   ancora meglio sarebbe fare piu' thread, o addirittura processi,
        #     per sfruttare i multicore
        #     il modulo multiprocessing ha multiprocessing.cpu_count()
        #     si potrebbe dividere le righe della griglia per il numero di cpu,
        #       e disegnarle con processi diversi
        #     ricordarsi che il problema e' nel disegno, e' quello che bisogna
        #       dividere, e purtroppo mi sa che non posso fare operazioni con
        #       wx su thread o processi diversi
        #   dopo un'analisi veloce ho visto che e' l'ultima parte ad essere
        #     lenta, quella in wxPython che disegna la griglia di pannelli
        #   il primo disegno e' assai piu' veloce di quelli successivi, come
        #     mai?
        #     distruggere l'oggetto della ScrolledWindow e rifare tutto daccapo
        #       ogni volta non risolve questo problema, i tempi rimangono
        #       invariati
        #   ad esempio SetBackgroundColour sembra prendere un buon 25% del
        #     tempo di disegno, trovare un'alternativa?
        #   per rappresentare una settimana dovrei moltiplicare il tempo per 7,
        #     ma se riuscissi a fondere la procedura di disegno in una griglia
        #     unica credo proprio che riuscirei a mantenere il tempo quasi
        #     invariato
        
        # Al momento ottengo la data di oggi, pero' questo va variato ************
        # Al momento converto tutte le date delle occorrenze in localtime, *******
        #     pero' potrei permettere di specificare nello scheduler se una
        #     data e' da considerare in localtime o UTC
        #   il punto e': se vado in giro per il mondo, ci sono cose che voglio
        #     fare sempre alla stessa ora locale, ma ci sono anche eventi che
        #     accadono alla stessa ora UTC in tutto il mondo, a prescindere
        #     dal fuso orario
        dtime = (int(_time.time()) - _time.altzone
                 ) // 86400 * 86400 + _time.altzone
        occs = organizer_api.get_daily_occurrences(dtime)
        
        # 1) Initialize cols
        #    use a dictionary to avoid duplicates
        cols = {}
        
        # 2) Creare tsdict con, come chiavi, il timestamp di ogni riga del *******
        #    giorno: creare 86400/secs righe, dove secs e' la risoluzione della
        #    griglia, cioe' l'altezza di una riga in secondi
        resolution = _CAL_RES
        tsdict = {}
        
        for i in range(86400 // resolution):
            t = dtime + resolution * i
            
            # Use a dictionary because it avoids checking for duplicates later
            # in ids
            tsdict[t] = {}
        
        # 3) Ad ogni riga associare una lista di tutte le occorrenze che *********
        #    rientrano in quella specifica riga
        for o in occs:
            id_ = o['id_']
            
            # Round start down to the previous step
            start = (o['start'] // resolution) * resolution
            
            # If end is not set, use resolution value
            if isinstance(o['end'], int):
                # Round end up to the next step
                end = (o['end'] // resolution) * resolution
            else:
                end = start + resolution
                
            for i in range((end - start) // resolution):
                tsdict[start + resolution * i][id_] = None
                
        print('====================')  # ***************************************************************
        for r in tsdict:  # ******************************************************
            print('TSDICT', _time.strftime('%H:%M', _time.localtime(r)),  # ******
                  tsdict[r])  # **************************************************
        
        # 4) Creare ids, un dizionario cosi' fatto:
        #    {id_1: {'w': width, 'h': duration, 'x1': lside, 'x2': rside,
        #                      'start': start, 'conflicts': [id_4, id_7, ...]},
        #     id_2: {...},
        #     ...
        #     id_4: {..., 'conflicts': [id_1, id_7, ...]},
        #     ...
        #     id_17: {...},
        #    }
        #    creare i 'conflicts';
        #    impostare 'w' al numero massimo di elementi tra le righe in cui
        #    appare l'item corrente, a rappresentare l'inverso della frazione
        #    di larghezza da occupare;
        #    come lside impostare a 0, cioe' inizializzo l'ascissa
        #    del lato sinistro combaciante col bordo sinistro della colonna
        #    del giorno; come rside impostare a 1, cioe' inizializzo l'ascissa
        #    del lato destro combaciante col bordo destro della colonna del
        #    giorno
        ids = {}
        
        # Do this _after_ creating tsdict
        for o in occs:
            # Qui duplico il codice usato sopra... *******************************
            id_ = o['id_']
            
            # Qui duplico il codice usato sopra... *******************************
            start = (o['start'] // resolution) * resolution
            
            # Qui duplico il codice usato sopra... *******************************
            if isinstance(o['end'], int):
                end = (o['end'] // resolution) * resolution
            else:
                end = start + resolution
                
            ids[id_] = {'h': (end - start) // resolution,
                        'y1': (start - dtime) // resolution,
                        'conflicts': {}}
            
            for i in range(ids[id_]['h']):
                row = tsdict[start + resolution * i]
                ids[id_]['conflicts'].update(row)
            
            del ids[id_]['conflicts'][id_]
                
        def recurse(id_, group):
            group.append(id_)
            
            for cid in ids[id_]['conflicts']:
                if cid not in group:
                    group = recurse(cid, group)
                    
            return group
        
        groups = []
        
        for o in occs:
            id_ = o['id_']
            
            for g in groups:
                if id_ in g:
                    break
            else:
                groups.append(recurse(id_, []))
        
        print('====================')  # ***************************************************************
        for d in ids:  # *********************************************************
            print('IDS1', d, ids[d])  # ******************************************
        
        # 5) Per ogni id_ di ids risolvere i conflitti in questo modo:
        #    A) se tutti gli 'x2' delle item in 'conflicts' sono == 1 (cioe'
        #       tutte le item arrivano al bordo destro della colonna del
        #       giorno) allora lascia l''x1' dell'item corrente a 0
        #       e imposta il suo 'x2' a 'x1' + 'w';
        #    B) se invece in 'conflicts' ci sono items con 'x2' < 1, trovare il
        #       massimo tra gli 'x2' < 1 e impostare l''x1' dell'item corrente
        #       a questo valore;
        #       impostare il suo 'x2' a 'x1 + 'w';
        #       cancellare da conflicts tutte le item con 'x2' < 1 e inoltre,
        #       per ognuna di queste item, cancellare l'item corrente nel
        #       'conflicts' della propria voce nel dizionario, dato che il
        #       conflitto e' stato appena risolto
        #    C) ripetere questo sotto-ciclo finche' non ci sono piu' conflitti
        
        # Provare un altro algoritmo per risolvere i conflitti: ******************
        #   (piu' semplicemente "a tentativi")
        #   * provare a mettere il rettangolo, che tanto e' di larghezza
        #     unitaria, nella prima colonna
        #   * se non ci sono intersezioni lascialo li' e cancella il conflitto
        #     reciproco tra le due occorrenze, altrimenti prova a metterlo
        #     nella colonna successiva e cosi' via, finche' sono risolti tutti
        #     i conflitti
        for group in groups:
            conflicts = {}
            
            for id_ in group:
                conflicts[len(ids[id_]['conflicts']) + 1] = None
            
            maxconflicts = max(tuple(conflicts.keys()))
            
            cols[maxconflicts] = None
                
            for id_ in group:
                ids[id_]['w'] = maxconflicts
                ids[id_]['x1'] = 0
                ids[id_]['x2'] = maxconflicts
        
        print('COLS', cols)  # ***************************************************
        
        conflicts = True
        
        while conflicts:
            conflicts = False
            
            for id_ in ids:
                if ids[id_]['conflicts']:
                    x2s = {}
                    
                    for cid in ids[id_]['conflicts']:
                        if ids[cid]['x2'] < ids[id_]['w']:
                            x2s[cid] = ids[cid]['x2']
                        
                    if x2s:
                        ids[id_]['x1'] = max(tuple(x2s.values()))
                    
                    ids[id_]['x2'] = ids[id_]['x1'] + 1
                        
                    for cid in x2s:
                        del ids[id_]['conflicts'][cid]
                        del ids[cid]['conflicts'][id_]
                        
                    if ids[id_]['conflicts']:
                        conflicts = True
        
        print('====================')  # ***************************************************************
        for d in ids:  # *********************************************************
            print('IDS2', d, ids[d])  # ******************************************
        
        # 6) Disegnare la colonna del giorno con un GridBagSizer, usando *********
        #    maxcolumns come numero di sotto-colonne
        if cols:
            mcmcols = lcmm(*tuple(cols.keys()))
        else:
            mcmcols = 1
            
        # Clear the Sizer (and delete children with the True option) to avoid
        # memory leak
        self.occgrid.Clear(True)
        
        print('CR', self.occgrid.GetCols(), self.occgrid.GetRows())  # ***********
        # Also rows must be reset every time
        self.occgrid.SetRows(86400 // _CAL_RES)
        self.occgrid.SetCols(mcmcols)
        print('MCM', mcmcols)  # *************************************************
        print('CR', self.occgrid.GetCols(), self.occgrid.GetRows())  # ***********
        
        for c in range(mcmcols):
            self.occgrid.AddGrowableCol(c)
        
        caltime = [_time.time()]  # **********************************************
        
        for id_ in ids:
            # Il colore va implementato in maniera piu' razionale ****************
            rcol = wx.Colour(red=random.randint(0, 255),  # **********************
                             green=random.randint(0, 255),
                             blue=random.randint(0, 255))
            
            opan = wx.Panel(self.occpanel, size=(-1, _ROW_HEIGHT))
            opan.SetBackgroundColour(rcol)
            
            vspan = ids[id_]['h']
            hspan = mcmcols // ids[id_]['w']
            row = ids[id_]['y1']
            col = hspan * ids[id_]['x1']
            
            print('POS', id_, row, col, vspan, hspan)  # *************************
            
            self.occgrid.Add(opan, (row, col), span=(vspan, hspan),
                             flag=wx.EXPAND | wx.ALL,
                             border=_CELL_BORDER)
        
        caltime.append(_time.time())  # ******************************************
        log.debug('Calendar redraw time: {}'.format(round(caltime[1] -  # ********
                                                          caltime[0], 3)))
        
        # Non so perche' ma se chiamo subito Layout non funziona, devo dargli ****
        #     un delay
        #self.occpanel.Layout()
        wx.FutureCall(5, self.Layout)


# Questa funzione varrebbe la pena di portarla in un modulo a parte **************
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


# Questa funzione varrebbe la pena di portarla in un modulo a parte **************
def gcdd(*args):
    return reduce(gcd, args)


# Questa funzione varrebbe la pena di portarla in un modulo a parte **************
def lcm(a, b):
    return a * b // gcd(a, b)


# Questa funzione varrebbe la pena di portarla in un modulo a parte **************
def lcmm(*args):
    return reduce(lcm, args)
