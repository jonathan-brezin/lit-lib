#!/usr/bin/env python3.5

""" test the dbg module """

from wildcardlookup import WildCardLookup

wcl1 = WildCardLookup("a, *_b, c_*, d*e")
ptn1 = list(wcl1.patterns());  ptn1.sort()
print("{0} should be ['*_b', 'a', 'c_*', d*e']".format(ptn1))
wcl2 = WildCardLookup("f", "*_b", "g_*", "*")
ptn2 = list(wcl2.patterns());  ptn2.sort()
print("{0} should be ['*', '*_b', 'f', g_*']".format(ptn2))
wcl3 = WildCardLookup("h", "b*", "*b", "k,l,m")
ptn3 = list(wcl3.patterns());  ptn3.sort()
print("{0} should be ['*b', 'b*', 'h', 'k', 'l', 'm']".format(ptn3))

wcl4 = wcl1 | wcl2
print("wck4 = wcl1 | wcl2 is "+str(wcl4.patterns()))
print("wcl1 < wcl4? {0}".format(wcl1<wcl4))

wcl5 = wcl1 & wcl2
print("wck5 = wcl1 & wcl2 is "+str(wcl5.patterns()))
print("wcl1 > wcl5? {0}".format(wcl1 > wcl5))

wcl6 = wcl1 ^ wcl2
print("wcl6 = wcl1 ^ wcl2 is "+str(wcl6.patterns()))

wcl7 = wcl1 - wcl2
print("wcl7 = wcl1 - wcl2 is "+str(wcl7.patterns()))

print("wcl1.anyMatched('x', 'a_b', 'y,c_d') is "+str(wcl1.anyMatched('x', 'a_b', 'y,c_d')))
print("wcl1.anyMatched('x', 'xa_yb', 'y,c_d') is "+str(wcl1.anyMatched('x', 'xa_yb', 'y,c_d')))
print("wcl1.anyMatched('x', 'xa_yb', 'y,cz_d') is "+str(wcl1.anyMatched('x', 'xa_yb', 'y,cz_d')))
