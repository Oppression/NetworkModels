#!/usr/local/bin/python

import cgi, cgitb

print "Content-type: text/html\n\n"

form = cgi.FieldStorage() 
if not (len(form.keys()) > 0):
    print "no form data"
    exit()


# Get data from fields
first_name = form.getvalue('first_name')
last_name  = form.getvalue('last_name')

s = ","
keys = s.join(form.keys())

print "keys = %s<p>" % keys
for key in form.keys():
    print "%s = %s<br>" % (key, form.getvalue(key))