#!/usr/local/bin/python

import sys, time, socket, MySQLdb, random, math, cgi, cgitb
from string import Template
#from scipy import stats

#cgitb.enable()

# array indices

race = 0
natlOrigin = 1
genderID = 2
sexualOrientation = 3
economicPower = 4
politicalViews = 5
physicalAbility = 6
educationLevel = 7
religiousViews = 8
fundamentalism = 9
reproductivePower = 10
lifespan = 11

labels = []

labels.append("Race")
labels.append("National Origin")
labels.append("Gender ID")
labels.append("Sexual Orientation")
labels.append("Economic Power")
labels.append("Political Views")
labels.append("Physical Ability")
labels.append("Education Level")
labels.append("Religious Views")
labels.append("Fundamentalism")
labels.append("Reproductive Power")
labels.append("Lifespan")

generationDuration = 600
debug = False

attr = {}


dbCols = ('id', 'generation', 'race', 'natlOrigin', 'genderID', 'sexualOrientation', 'economicPower', 'politicalViews', \
    'physicalAbility', 'educationLevel', 'religiousViews', 'fundamentalism', 'reproductivePower', 'lifespan', 'born', 'label', 'tithe')
    
processCols = ('race', 'genderID')

submitTemplateFile = "/usr/local/O3/www/submit.template.html"
checkTemplateFile = "/usr/local/O3/www/check.template.html"

#startTime = int(time.time())
startTime = 1484567200

numAttrs = len(labels)

db = MySQLdb.connect("localhost", "root", "sa", "o3")
c = db.cursor(MySQLdb.cursors.DictCursor)


def dbStore(who):
    keysDone = 0
    numKeys = len(dbCols)
    keyString = ''
    valString = ''
    for key in who.attrs.keys():
        keyString += key
        if key == 'label':
            valString += "'%s'" % who.attrs[key]
        else:
            valString += "%s" % who.attrs[key]
        keysDone += 1
        if debug: print "%d %s" % (keysDone, key)
        if (keysDone < numKeys):
            keyString += ", "
            valString += ", "
    
    sql = "insert into people (%s) values (%s)" % (keyString, valString)
    if debug: print "dbStore sql = %s" % sql    
    c.execute(sql)
    db.commit()

    
def dbGetNextID():
    sql = "select max(id) from people"
    c.execute(sql)
    nextID = c.fetchone()['max(id)']
    if nextID >= 0:
        return nextID+1
    else:
        return 0


def getEconPower(column, bin):
    sql = "select min(born) as minBorn from people where %s between %d and %d" % (column, 10*bin, 10*(bin+1))
    if debug: print sql
    c.execute(sql)
    res = c.fetchone()
    minBorn = res['minBorn']
    rightNow = int(time.time())
    econPow = int(float((rightNow - minBorn))/(rightNow-startTime)*100)
    if debug: print "econPower(%s, %d) = %d" % (column, bin, econPow)
    return econPow

def getBin(id, column):
    sql = "select %s from people where id = %d" % (column, id)
    c.execute(sql)
    res = c.fetchone()[column]
    bin = res/10
    return bin
    
    
def getGeneration(born):
    sql = "select min(born) as minBorn from people"
    c.execute(sql)
    res = c.fetchone()
    minBorn = res['minBorn']
    generation = (born-minBorn)/generationDuration
    return generation

def getGenerationOffset():
    sql = "select min(generation) as minGen from people where generation > 1";
    c.execute(sql)
    res = c.fetchone()
    return res['minGen']-1

def getMaxGeneration():
    sql = "select max(generation) as maxGen from people";
    c.execute(sql)
    res = c.fetchone()
    return res['maxGen']


def oppFactor(column, bin, generation):
    lo = 10*bin
    hi = 10*(bin+1)
    sql = "select count(id) as count, avg(fundamentalism) as avgFun, avg(generation) as avgEcon from people where generation <= %d and %s between %d and %d" % (generation, column, 10*bin, 10*(bin+1))
    #print sql
    c.execute(sql)
    res = c.fetchone()
    if ('count' in res) and ('avgFun' in res) and ('avgEcon' in res) and (res['count'] > 0):
        count = float(res['count'])
        avgFun = float(res['avgFun'])
        avgEconPow = float(res['avgEcon'])
        #print "oppFactor(%s, %d) = %f, %f, %f, %f\n" % (column, bin, count, avgFun, avgEconPow, count*avgFun*avgEconPow)
        return(count*avgFun*avgEconPow)
    else:
        return 0
    
def opp(column, bin1, bin2, generation): # return freedom bin subfactor of bin 1 relative to oppression from bin2
    opp1 = oppFactor(column, bin1, generation)
    opp2 = oppFactor(column, bin2, generation)
    #print "opp says: opp1 = %d opp2 = %d" % (opp1, opp2)
    
    if opp1 > opp2:
        #score = 100
        score = int(100*float(opp1-opp2)/(opp1+opp2))
    elif (opp1 == 0) and (opp2 == 0):
        score = -1
    else:
        score = int(100 - 100*float(opp2-opp1)/(opp1+opp2))
    #print "score = %f" % score
    #print "opp(%d) = %f, opp(%d) = %f" % (bin1, opp1, bin2, opp2)
    #print "opp(%s, %d, %d, %d) = %d" % (column, bin1, bin2, generation, score)
    return score
    
        
def freedomSubfactor(id, column, generation): # return freedom subfactor for attribute
    sql = "select %s from people where id = %d" % (column, id)
    c.execute(sql)
    res = c.fetchone()
    bin = res[column] // 10
    sumFsf = 0
    count = 0
    for i in range(0,10):
        if (i != bin):
            sf = opp(column, bin, i, generation)
            #print "opp(%d, %d) = %f" % (bin, i, sf)
            if (sf >=0):
                sumFsf += sf
                count += 1
    if debug: print "sumFsf = %d" % sumFsf
    fsf = int(sumFsf/count)
    if debug: print "fsf = %d" % fsf
    return fsf
    
def freedomFactor(id, generation):
    ff = 0
    count = 0
    for i in processCols:
        fsf = freedomSubfactor(id, i, generation)
        ff += fsf
        count += 1
        #if debug: print "fsf(%s) = %f" % (i, fsf)
        if debug: print "freedom subfactor %s = %d" % (i, fsf)
    return int(float(ff)/count)
    
def binPopulation(column, bin, generation):
    lo = 10*bin
    hi = 10*(bin+1)
    sql = "select count(id) as count from people where generation <= %d and %s between %d and %d" % (generation, column, lo, hi)
    c.execute(sql)
    res = c.fetchone()
    return res['count']

def totalPopulation(generation):
    sql = "select count(id) as count from people where generation <= %d" % (generation)
    c.execute(sql)
    res = c.fetchone()
    return res['count']

def getLabel(column, bin):
    sql = "select label from categorylabels where category = '%s' and bin = %d" % (column, bin)
    c.execute(sql)
    res = c.fetchone()
    return res['label']
  
def getScores(label, generation):
    #print "check value for %s" % label
    sql = "select id, generation from people where label = '%s'" % label
    c.execute(sql)
    res = c.fetchone()
    id = int(res['id'])
    genOffset = getGenerationOffset()
    bornGeneration = int(res['generation'])
    outStr = "<pre>\n"
    outStr += "Freedom Report for %s\n\nBorn in generation %d\n" % (label, bornGeneration-genOffset)
    outStr += "Simulation ends at generation %d\n" % (getMaxGeneration() - genOffset)
    for key in processCols:
        bin = getBin(id, key)
        label = getLabel(key, bin)
        outStr += "%s category: %s\n" % (key, label)   
   
    outStr += "\n" 
    for i in range(bornGeneration, generation):
        outStr += "Generation %d:\n" % (i - genOffset)
        #print "Generation %d: " % i
        #print "i = %d, bornGeneration = %d, generation = %d" % (i, bornGeneration, generation)
        myScores = {}
        for key in processCols:
            myScores[key] = freedomSubfactor(id, key, i)
            bin = getBin(id, key)
            binPop = binPopulation(key, bin, i)
            totalPop = totalPopulation(i)
            label = getLabel(key, bin)
            outStr += "\t%-10s:\tfreedom sub-score = %d\t\t" % (key, myScores[key])
            outStr += "%% of total population in your category = %.2f%% (%d/%d)\n" % (100*float(binPop)/totalPop, binPop, totalPop)
            #print "%s: %d\t" % (key, myScores[key])
        totalFF = freedomFactor(id, i)
        outStr += "\t<b>Total Freedom Score: %d</b>\n\n" % totalFF
    outStr += "</pre>"
    #print outStr
    return outStr


class Person:
    
    attrs = {}

    def __init__(self, myAttr):
    
        self.attrs = myAttr
        self.attrs['id'] = dbGetNextID()
        self.attrs['born'] = int(time.time())
        self.attrs['generation'] = getGeneration(self.attrs['born'])
        if not 'label' in self.attrs:
            labelStr = "%d" % self.attrs['id']
            self.attrs['label'] = labelStr
        else:
            self.attrs['label'] = self.attrs['label'].upper()
        if not 'tithe' in self.attrs:
            self.attrs['tithe'] = 0
        
        for key in dbCols:
            if not (key in self.attrs):
                self.attrs[key] = int(random.random() * 100)

        dbStore(self)

    def dump(self):
        if debug: print "ID: ", self.id
        if debug: print "Parent: ", self.parent
        if debug: print "Generation: ", self.generation
        for x in range(0, numAttrs):
            if debug: print labels[x], ": ", self.attrs[x]
        if debug: print
        

form = cgi.FieldStorage() 
if (len(form.keys()) > 0):
    for key in form.keys():
        attr[key] = form.getvalue(key)
    web = True
    label = form.getvalue('label').upper()
    print "Content-type: text/html\n\n"
else:
    args = sys.argv[1:]
    for arg in args:
        (key, val) = arg.split('=',1)
        attr[key] = val
    label = attr['label'].upper()
    web = False


if 'check' in attr:
    myScores = {}
    #sql = "select max(generation) as maxGen from people"
    #c.execute(sql)
    #res = c.fetchone()
    currentGeneration = getMaxGeneration() +1
    outStr = getScores(label, currentGeneration)
    if web == True:
        f = open(checkTemplateFile, 'r')
        tmpl = f.read()
        f.close()
        s = Template(tmpl)
        output = s.substitute(label=label, scores=outStr)
        print output
    else:
        print outStr
else:
    p = Person(attr)

    if web == True:
        f = open(submitTemplateFile, 'r')
        tmpl = f.read()
        f.close()
        s = Template(tmpl)
        outStr = getScores(attr['label'])
        output = s.substitute(label=p.attrs['label'], scores='')
        print output

            
