#!/usr/bin/python

outfile = "walks.rou.xml"
startEdge = "E0"
endEdge = "E0.0"
departTime = 0.0
departPos = -30.0
arrivalPos = 100.0
number = 100

xml_string = "<routes>\n"  
for i in range(number):
    xml_string += '    <person depart="%f" id="p%d" departPos="%f" >\n' % (departTime, i, departPos)
    xml_string += '        <walk edges="%s %s" arrivalPos="%f"/>\n' % (startEdge, endEdge, arrivalPos)
    xml_string += '    </person>\n'
xml_string += "</routes>\n"

with open(outfile, "w") as f:
    f.write(xml_string)
    