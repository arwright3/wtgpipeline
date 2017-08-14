
import os
for [filter,type] in [['b','skyflat']]: #['i','skyflat'],['z','skyflat'],['z','domeflat']]:
	print type, filter
	if type == 'skyflat':
		if filter == 'b':   
	        	brackets = [[1345,1729],[1845,2555]] #[1345,1729],[1845,2555],[1345,1524],[1640,1729],[1845,1998],[2316,2555],[1340,1345],[1490,1495],[1638,1643],[1666,1672],[1725,1730],[1845,1849],[1870,1875],[1877,1883],[1900,1907],[1928,1933],[1994,2003],[2312,2319],[2523,2529],[2729,2735],[2876,2882]]
	        if filter == 'v':
	        	brackets = [[1550,1800],[1801,2399],[2400,10000],[1550,1581],[1703,1758],[1842,1874],[2198,2319],[2407,2556]]
	        if filter == 'r':
	        	brackets = [[1403,2000],[2001,10000],[1496,1497],[1526,1554],[1639,1694],[2196,2261],[2732,2823]]
	        if filter == 'i':
	        	brackets = [[1551,1755],[1877,2052],[2315,2731]] #[1551,1611],[1877,2731],[1551,1554],[1577,1611],[1755,1755],[1877,1903],[2052,2558],[2731,2731],[1548,1553],[1582,1590],[1606,1614],[1723,1732],[1752,1758]]
	        if filter == 'z':
	        	brackets = [[1555,1639],[1843,1846],[1902,2268]] #[[1523,1846],[1878,2668],[1523,1639],[1843,1846],[1878,1902],[1993,1994],[2268,2668],[1521,1525],[1553,1557],[1637,1642],[1841,1849],[1875,1881],[1900,1906],[1991,1997]]

	if type == 'domeflat':
		if filter == 'b':
			brackets = [[1340,1345],[1490,1495],[1638,1643],[1666,1672],[1725,1730],[1845,1849],[1870,1875],[1877,1883],[1900,1907],[1928,1933],[1994,2003],[2312,2319],[2523,2529],[2729,2735],[2876,2882]]
		if filter == 'i':
			brackets = [[1551,1611],[1728,1903],[2439,2529]] #[[[1548,1553],[1582,1590],[1606,1614],[1723,1732],[1752,1758]]
		if filter == 'z':
			brackets = [[1523,1642],[1843,1879],[1901,2268]] #[[[1521,1525],[1553,1557],[1637,1642],[1841,1849],[1875,1881],[1900,1906],[1991,1997]]

	if filter == 'b': longfilter = 'W-J-B'                                                                                                                                             	
	if filter == 'i': longfilter = 'W-C-IC'                                                                                                                                             	
        if filter == 'z': longfilter = 'W-S-Z+'
        ww = 0
        for brack in brackets:
        	ww = ww + 1
		for chipnum in range(1,11):
	        	strg = 'cp ' + os.environ['subdir'] + '2007-07-18_' + type + '_' + filter + '/' + type.upper() + '/' + str(brack[0]) + '_' + str(brack[1]) + '_MEDIAN_3.0_3.0_chip' + str(chipnum) + '.fits ' + os.environ['subdir'] + 'SUBARU_10_2_' + longfilter + '_' + type.upper() + '/SET' + str(ww) + '/' + type.upper() + '_SET' + str(ww) + '_' + str(chipnum) + '.fits'
        		print strg
			try: os.system(strg)
			except:
				print 'didnt work'
				raw_input()
			rr = "#GABODSID\nMIN=" + str(brack[0]) + "\nMAX=" + str(brack[1])
			r2 = open(os.environ['subdir'] + 'SUBARU_10_2_' + longfilter + '_' + type.upper() + '/SET' + str(ww) + '/gabodsid','w')
			print rr
			r2.write(rr)
			r2.close()
			
