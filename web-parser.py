import slate
import string
import re
import sys
import urllib2,httplib
import csv
from StringIO import StringIO
from flask import Flask,request,abort,render_template,send_file
import datetime

PDF_URL='https://www.dmr.nd.gov/oilgas/daily/%s/dr%s.pdf'
START='PERMIT LIST'
STOP='ADDITIONAL INFORMATION'
REGEXP=r"""#\d+\s{1,}-\s{1,}[^#]*API\s#\d{2}-\d{3}-\d{5}"""

app=Flask(__name__,static_url_path='')
app.config.from_object(__name__)

@app.route('/', defaults = {'input_data':None},methods=['GET','POST'])
def mainpage(input_data):
    if request.method=='GET':
        return render_template('index.html')
    if request.method=='POST':
        input_data=request.form.get('input','none').strip()
        if not re.match(r"\d\d/\d\d/\d\d\d\d",input_data):
            abort(404)
        date=input_data
        try:
            month,day,year=map(int,date.split('/'))
            provided_date=datetime.date(year,month,day)
            diff=provided_date-datetime.date.today()
            if diff.days>-1:
                abort(404)
        except ValueError:
            abort(404)

        year=date.split('/')[-1]
        short_date=''.join(date.split('/')[:-1])+year[2:]
        url=PDF_URL % (year, short_date)
        try:
            f=urllib2.urlopen(url)
        except (httplib.HTTPException,urllib2.HTTPError,urllib2.URLError):
            abort(404)
        #API #33-053-06418
        pdf_in_mem=StringIO(f.read())
        of=StringIO()
        writer=csv.writer(of)
        doc=slate.PDF(pdf_in_mem)
        doc_as_string=''.join(doc)
        doc_filtered=''.join(c for c in doc_as_string if c!=chr(12))
        s=doc_filtered[doc_filtered.find(START)+len(START):doc_filtered.find(STOP)].strip()
        if re.search(REGEXP,s):
            for line in re.findall(REGEXP,s):
                line=line.replace(', INC',' INC')
                line=line.replace(', LLC',' LLC')
                number,rest=line.split('  -  ')
                writer.writerow([number]+rest.split(','))
                of.flush()
        of.seek(0)
        filename='{}.csv'.format(date.replace('/','-'))
        return send_file(of, mimetype='text/csv',attachment_filename=filename,as_attachment=True)

if __name__=='__main__':
    app.debug=False
    app.run(host='0.0.0.0')
