def sextract(filter,cluster):
    #from config_bonn import cluster
    import utilities
    import os, re, bashreader, sys, string
    from glob import glob
    from copy import copy

    dict = bashreader.parseFile('progs.ini')
    for key in dict.keys():
        os.environ[key] = str(dict[key])

    TEMPDIR = '/tmp/'
    PHOTCONF = './photconf/'

    path='/nfs/slac/g/ki/ki05/anja/SUBARU/%(cluster)s/' % {'cluster':cluster}

    search_params = {'path':path, 'cluster':cluster, 'filter':filter, 'PHOTCONF':PHOTCONF, 'DATACONF':os.environ['DATACONF'], 'TEMPDIR':TEMPDIR,'fwhm':1.00} 

    searchstr = "/%(path)s/*%(fil_directory)s/SCIENCE/*fits" % search_params
    print searchstr
    files = glob(searchstr)
    if len(files) == 0: return []
    files.sort()
    print files
    exposures = {} 
    # first 30 files
    print files[0:30]
    for file in files:
        if string.find(file,'wcs') == -1 and string.find(file,'.sub.fits') == -1:
            res = re.split('_',re.split('/',file)[-1])                                        
            print res
            if not exposures.has_key(res[0]): exposures[res[0]] = {}
            if not exposures[res[0]].has_key('images'): exposures[res[0]]['images'] = [] 
            if not exposures[res[0]].has_key('keywords'): exposures[res[0]]['keywords'] = {} 
            exposures[res[0]]['images'].append(file) # res[0] is the root of the image name
            print 'hey', file
            reload(utilities)

            import re
            res = re.split('/',file)   
            for r in res:
                if string.find(r,filter):
                    exposures[res[0]]['keywords']['date'] = r.replace(filter + '_','')
                    exposures[res[0]]['keywords']['fil_directory'] = r 

            if not exposures[res[0]]['keywords'].has_key('ROTATION'): #if exposure does not have keywords yet, then get them
                kws = utilities.get_header_kw(file,['ROTATION','GABODSID']) # return KEY/NA if not SUBARU 
                exposures[res[0]]['keywords']['filter'] = filter
                print kws.keys()
                for kw in kws.keys(): 
                    exposures[res[0]]['keywords'][kw] = kws[kw]
                    print kw, kws[kw]


    print 'hey2!!!!!!'
    print exposures
    #raw_input()
    #exposures = {exposures.keys()[0]: exposures[exposures.keys()[0]]}
    lkeys = len(exposures.keys()) 
    if lkeys > 6: lkeys = 6
    expnew = {}
    for i in range(lkeys):
        expnew[exposures.keys()[i]] = exposures[exposures.keys()[i]]
    exposures = expnew

    print exposures

    print 'stop1'
    #temporary method

    run_sex = 1

    for kw in exposures.keys(): # now go through exposure by exposure
        outfinal = TEMPDIR + 'paste_' + kw + '.cat'
        exposures[kw]['pasted_cat'] = outfinal
        if run_sex: 
            exposure = exposures[kw]                            
            print kw, exposure['images']
            children = []
            print exposure['images']
            print 'hey!!!!!!'
            for image in exposure['images']:
                child = os.fork()
                if child:
                    children.append(child)
                else:
                    params = copy(search_params)     
                    params['GAIN'] = 1.000 #float(exposure['keywords']['GAIN'])
                    params['PIXSCALE'] = float(exposure['keywords']['PIXSCALE'])
                    
                    ROOT = re.split('\.',re.split('\/',image)[-1])[0]
                    params['ROOT'] = ROOT
                    NUM = re.split('O',re.split('\_',ROOT)[1])[0]
                    params['NUM'] = NUM
                    print ROOT
                    weightim = "/%(path)s/%(fil_directory)s/WEIGHTS/%(ROOT)s.weight.fits" % params
                    from glob import glob
                    if len(glob(weightim)) == 0:
                        weightim = "/%(path)s/%(fil_directory)s/WEIGHTS/globalweight_%(NUM)s.fits" % params
                    params['weightim'] = weightim 
                    flagim = "/%(path)s/%(fil_directory)s/WEIGHTS/globalflag_%(NUM)s.fits" % params
                    finalflagim = TEMPDIR + "flag_%(ROOT)s.fits" % params 
                    params['finalflagim'] = flagim
                    #command = "ic -p 16 '1 %2 %1 0 == ?' " + weightim + " " + flagim + " > " + finalflagim
                    #utilities.run(command)
                    command = "sex /%(path)s/%(fil_directory)s/SCIENCE/%(ROOT)s.fits -c %(PHOTCONF)s/singleastrom.conf.sex \
                                -FLAG_IMAGE ''\
                                -FLAG_TYPE MAX\
                                -CATALOG_NAME %(TEMPDIR)s/seeing_%(ROOT)s.cat \
                                -FILTER_NAME %(PHOTCONF)s/default.conv\
                                -CATALOG_TYPE 'ASCII' \
                                -DETECT_MINAREA 5 -DETECT_THRESH 5.\
                                -ANALYSIS_THRESH 5 \
                                -WEIGHT_IMAGE %(weightim)s\
                                -WEIGHT_TYPE MAP_WEIGHT\
                                -FLAG_TYPE MAX\
                                -FLAG_IMAGE %(finalflagim)s\
                                -PARAMETERS_NAME %(PHOTCONF)s/singleastrom.ascii.flag.sex" %  params 
                                                                                                                                                                                                                                                                                                                                                                                                                          
                    print command
                    os.system(command)
                                                                                                                                                                                                                                                                                                                                                                                                                          
                    sys.exit(0)
            for child in children:  
                os.waitpid(child,0)
            command = 'cat ' + TEMPDIR + 'seeing_' +  kw + '*cat > ' + TEMPDIR + 'paste_seeing_' + kw + '.cat' 
            utilities.run(command)

                                                                                                                                                                                                                                                                                                                                                                                                                          
            file_seeing = TEMPDIR + '/paste_seeing_' + kw + '.cat'
            PIXSCALE = float(exposure['keywords']['PIXSCALE'])
            reload(utilities)
            print file_seeing, kw, PIXSCALE, exposure['keywords']['PIXSCALE'] 
            fwhm = utilities.calc_seeing(file_seeing,10,PIXSCALE)
            
                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                          
            # get the CRPIX values for 
            image = exposure['images'][0]
            print image
            res = re.split('\_\d+',re.split('\/',image)[-1])
            print res
            imroot = "/%(path)s/%(fil_directory)s/SCIENCE/" % search_params
            im = imroot + res[0] + '_1' + res[1] 
            crpixzero = utilities.get_header_kw(im,['CRPIX1','CRPIX2'])
                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                          
            children = []
            for image in exposure['images']:
                child = os.fork()
                if child:
                    children.append(child)
                else:
                    params = copy(search_params)  
                    params['fwhm'] = fwhm
                    params['GAIN'] = 1.000 #float(exposure['keywords']['GAIN'])
                    params['PIXSCALE'] = float(exposure['keywords']['PIXSCALE'])
                                                                                                                                                                                                                                                                                                                                                                                                                          
                    ROOT = re.split('\.',re.split('\/',image)[-1])[0]
                    params['ROOT'] = ROOT
                    NUM = re.split('O',re.split('\_',ROOT)[1])[0]
                    params['NUM'] = NUM
                    print ROOT


                    weightim = "/%(path)s/%(fil_directory)s/WEIGHTS/%(ROOT)s.weight.fits" % params          
                    from glob import glob
                    if len(glob(weightim)) == 0:
                        weightim = "/%(path)s/%(fil_directory)s/WEIGHTS/globalweight_%(NUM)s.fits" % params
                    params['weightim'] = weightim 
                    
                    finalflagim = TEMPDIR + "flag_%(ROOT)s.fits" % params 

                    flagim = "/%(path)s/%(fil_directory)s/WEIGHTS/globalflag_%(NUM)s.fits" % params
                    params['finalflagim'] = flagim                                             
                    im = "/%(path)s/%(fil_directory)s/SCIENCE/%(ROOT)s.fits" % params
                    crpix = utilities.get_header_kw(im,['CRPIX1','CRPIX2'])
                                                                                                                                                                                                                                                                                                                                                                                                                          
                    command = "sex /%(path)s/%(fil_directory)s/SCIENCE/%(ROOT)s.fits -c %(PHOTCONF)s/phot.conf.sex \
                    -PARAMETERS_NAME %(PHOTCONF)s/phot.param.sex \
                    -CATALOG_NAME %(TEMPDIR)s/%(ROOT)s.cat \
                    -FILTER_NAME %(DATACONF)s/default.conv\
                    -FILTER  Y \
                    -FLAG_TYPE MAX\
                    -FLAG_IMAGE %(finalflagim)s\
                    -WEIGHT_IMAGE %(weightim)s\
                    -SEEING_FWHM %(fwhm).3f \
                    -DETECT_MINAREA 3 -DETECT_THRESH 3 -ANALYSIS_THRESH 3 \
                    -MAG_ZEROPOINT 27.0 \
                    -GAIN %(GAIN).3f \
                    -WEIGHT_TYPE MAP_WEIGHT" % params
                    #-CHECKIMAGE_TYPE BACKGROUND,APERTURES,SEGMENTATION\
                    #-CHECKIMAGE_NAME /%(path)s/%(fil_directory)s/PHOTOMETRY/coadd.background.fits,/%(path)s/%(fil_directory)s/PHOTOMETRY/coadd.apertures.fits,/%(path)s/%(fil_directory)s/PHOTOMETRY/coadd.segmentation.fits\
                                                                                                                                                                                                          
                    catname = "%(TEMPDIR)s/%(ROOT)s.cat" % params
                    print command
                    utilities.run(command,[catname])
                    command = 'ldacconv -b 1 -c R -i ' + TEMPDIR + params['ROOT'] + '.cat -o ' + TEMPDIR + params['ROOT'] + '.conv'
                    print command
                    utilities.run(command)
                    # Xpos_ABS is difference of CRPIX and zero CRPIX
                    command = 'ldaccalc -i ' + TEMPDIR + params['ROOT'] + '.conv -o ' + TEMPDIR + params['ROOT'] + '.newpos -t OBJECTS -c "(Xpos + ' + str(float(crpix['CRPIX1']) - float(crpixzero['CRPIX1'])) + ');" -k FLOAT -n Xpos_ABS "" -c "(Ypos + ' + str(float(crpix['CRPIX2']) - float(crpixzero['CRPIX2'])) + ');" -k FLOAT -n Ypos_ABS "" -c "(Ypos*0 + ' + str(params['NUM']) + ');" -k FLOAT -n CHIP "" ' 
                    print command
                    utilities.run(command)
                    sys.exit(0)
            for child in children:  
                os.waitpid(child,0)

            outcat = TEMPDIR + 'tmppaste_' + kw + '.cat'
            command = 'ldacpaste -i ' + TEMPDIR + kw + '*newpos -o ' + outcat
            print command
            utilities.run(command)
            os.system('ldactoasc -i ' + outcat + ' -b -s -k MAG_APER MAGERR_APER -t OBJECTS > /tmp/' + kw + 'aper')
            os.system('asctoldac -i /tmp/' + kw + 'aper -o /tmp/' + kw + 'cat1 -t OBJECTS -c ./photconf/MAG_APER.conf')
            os.system('ldacjoinkey -i ' + outcat + ' -p /tmp/' + kw + 'cat1 -o ' + outfinal + ' -k MAG_APER1 MAG_APER2 MAGERR_APER1 MAGERR_APER2')


    return exposures

def match(exposures,cluster):
    import os
    print exposures
    sdsscat ='/nfs/slac/g/ki/ki05/anja/SUBARU/%(cluster)s/PHOTOMETRY/sdss.cat' % {'cluster':cluster}
    path='/nfs/slac/g/ki/ki05/anja/SUBARU/%(cluster)s/' % {'cluster':cluster}
    illum_path='/nfs/slac/g/ki/ki05/anja/SUBARU/ILLUMINATION/' % {'cluster':cluster}
    os.system('mkdir -p ' + path + 'PHOTOMETRY/ILLUMINATION/') 
    from glob import glob
    if len(glob(sdsscat)) == 0:
        image = exposures[exposures.keys()[0]]['images'][0]
        print image
        command = 'python retrieve_sdss.py ' + image + ' ' + sdsscat
        print command    
        os.system(command)

    for exposure in exposures.keys():
        print exposure + 'aa'
        catalog = exposures[exposure]['pasted_cat']
        filter = exposures[exposure]['keywords']['filter']
        ROTATION = exposures[exposure]['keywords']['ROTATION']
        GABODSID = exposures[exposure]['keywords']['GABODSID']
        print catalog
        outcat = path + 'PHOTOMETRY/ILLUMINATION/matched_' + exposure + '_' + filter + '_' + ROTATION + '.cat'               
        linkdir = illum_path + '/' + filter + '/' + ROTATION + '/'               
        outcatlink = linkdir + 'matched_' + exposure + '_' + cluster + '_' + GABODSID + '.cat' 
        os.system('mkdir -p ' + linkdir)
        command = 'match_any.sh ' + catalog + ' ' + sdsscat + ' ' + outcat
        print command

        os.system(command)

        exposures[exposure]['matched_cat'] = outcat
        os.system('rm ' + outcatlink)
        command = 'ln -s ' + outcat + ' ' + outcatlink
        print command
        os.system(command)


    return exposures



def fit_color(cluster):
    from photo_abs_new import *        
    infile='/tmp/input.asc'    
    outfile='/tmp/photo_res'
    extinction=-0.2104
    color=0.0
    night=-1
    label='imz'
    sigmareject=3
    step='STEP_1'
    bandcomp='z'
    color1which='imz'
    color2which='imz'
    extcoeff=None

    #### FIX COLOR COEFF
    data, airmass, color1, color2, magErr, X, Y = readInput(infile)
    pdict = {'zp':24,'extcoeff':extcoeff,'color1':0,'color2':0}
    #write input quantities to dictionary 
    var_names = {'bandcomp':bandcomp, 'color1which':color1which , 'color2which':color2which, 'sigmareject':sigmareject, 'cluster':cluster, 'label':label}
    #define the fits you want to make
    fits = [{'model':[{'name':'zp','term':['zp'],'value':pdict['zp']},{'name':'color1','term':['color1'],'value':pdict['color1']},{'name':'color2','term':['color2'],'value':pdict['color2']},{'name':'X','term':['X'],'value':0},{'name':'YTY','term':['Y','Y'],'value':0},{'name':'XTX','term':['X','X'],'value':0},{'name':'Y','term':['Y'],'value':0},{'name':'XTY','term':['X','Y'],'value':0}], \
                'fixed':[], \
                'apply' : ['zp','color1','color2','X','Y','XTY','XTX','YTY'], \
                'plots':[{'xaxis_var':'color1','term_names':['color1']}]},
            {'model':[{'name':'zp','term':['zp'],'value':pdict['zp']},{'name':'color1','term':['color1'],'value':pdict['color1']},{'name':'color2','term':['color2'],'value':pdict['color2']}], \
                'fixed':[], \
                'apply':[], \
                'plots':[{'xaxis_var':'color1','term_names':['color1']},{'xaxis_var':'color2','term_names':['color2']}]}, \
             {'model':[{'name':'zp','term':['zp'],'value':pdict['zp']},{'name':'color1','term':['color1'],'value':pdict['color1']}], \
                'fixed':[], \
                'apply': [], \
                'plots':[{'xaxis_var':'color1','term_names':['color1']}]}]

    #generate a class for the fit model
    for i in range(len(fits)):
        print fits[i]['apply']
        j = phot_funct(fits[i]['model'],fits[i]['fixed'],fits[i]['apply'])
        fits[i]['class'] = j
        print i
        print fits[i]

    fits = photCalib(data, airmass, color1, color2, magErr, X, Y, fits, sigmareject)

    #make a label for the fitting model                                             
    for i in range(len(fits)):
        jj = [] 
        for term in fits[i]['model']:   
            print term                                               
            jj.append(reduce(lambda x,y: x  + 'T' + y,term['term']))
        model =  reduce(lambda z,w: z + 'P' + w, jj)
        fits[i]['class'].fitvars['model_name'] = model
    jj = [] 
    for term in fits[i]['fixed']:   
        print term
        jj.append(reduce(lambda x,y: x  + 'T' + y,term['term']))
    if len(jj): 
        model =  reduce(lambda z,w: z + 'P' + w, jj)
    else: model = ''
    fits[i]['class'].fitvars['fixed_name'] = model

    corr_data = fits[0]['class'].apply_fit(data,airmass,color1,color2,magErr,X,Y)    
    calcDataIllum(20000,20000,1000, corr_data, airmass, color1, color2, magErr, X, Y)
    import sys
    sys.exit(0) 

    yesno = raw_input('make illumination image?')
    if len(yesno) > 0: 
        if yesno[0] == 'y' or yesno[0] == 'Y': 
            calcIllum(12000,12000,100,fits)
            
    #makePlotsNew(data, airmass, color1, color2, X, Y, outfile, fits, var_names)



def phot(files,filter,ROTATION): 

    import utilities

    info = {'B':{'filter':'g','color1':'gmr','color2':'umg','EXTCOEFF':-0.2104,'COLCOEFF':0.0},\
        'W-J-B':{'filter':'g','color1':'gmr','color2':'umg','EXTCOEFF':-0.2104,'COLCOEFF':0.0},\
        'W-J-V':{'filter':'g','color1':'gmr','color2':'rmi','EXTCOEFF':-0.1202,'COLCOEFF':0.0},\
        'W-C-RC':{'filter':'r','color1':'rmi','color2':'gmr','EXTCOEFF':-0.0925,'COLCOEFF':0.0},\
        'W-C-IC':{'filter':'i','color1':'imz','color2':'rmi','EXTCOEFF':-0.02728,'COLCOEFF':0.0},\
        'W-S-Z+':{'filter':'z','color1':'imz','color2':'rmi','EXTCOEFF':0.0,'COLCOEFF':0.0}}
    
    #filters = ['W-J-V','W-C-RC','W-C-IC','W-S-Z+']
    #cluster = 'MACS2243-09'
    
    #filters = ['W-S-Z+'] # ['W-J-B','W-J-V','W-C-RC','W-C-IC','W-S-Z+']
    
    base='/nfs/slac/g/ki/ki05/anja/SUBARU/' + cluster + '/PHOTOMETRY/cat/'
    base=''


    #file='all_merg.cat' 
    #file='matched_SUPA0055758.cat'
    #file = exposures[exposures.keys()[0]]['matched_cat']
    mag='MAG_APER2'
    magerr='MAGERR_APER2'
    
    import mk_saturation_plot,os,re
    os.environ['BONN_TARGET'] = cluster
    os.environ['INSTRUMENT'] = 'SUBARU'

    stars_0 = []
    stars_90 = []

    for file in files:
        #file = exposures[exposure]['matched_cat']

        #ROTATION = exposures[exposure]['keywords']['ROTATION']

        import re
        res = re.split('\/',file.replace('.fits',''))
        res = re.split('\_',res[-1])

        print res

        #ROTATION = res[0]

        


        print ROTATION 
        #raw_input()
        import os
        ppid = str(os.getppid())
        from glob import glob
        if 1: #len(glob(file)):
            
            for filter in [filter]:                                                                                                                                                                                                                                                               
                print 'filter', filter
                os.environ['BONN_FILTER'] = filter 
                dict = info[filter]
                 
                #run('ldacfilter -i ' + base + file + ' -o /tmp/good.stars -t PSSC\
                #            -c "(Flag=0) AND (SEx_CLASS_STAR_' + filter + '>0.90);"',['/tmp/good.stars'])
            
                utilities.run('ldacfilter -i ' + base + file + ' -o /tmp/good.stars' + ppid + ' -t PSSC\
                      -c "(((SEx_IMAFLAGS_ISO=0 AND SEx_CLASS_STAR>0.5) AND (SEx_Flag=0)) AND Flag=0);"',['/tmp/good.stars' + ppid])
            
                #run('ldacfilter -i ' + base + file + ' -o /tmp/good.stars -t PSSC\
               #             -c "(SEx_CLASS_STAR>0.00);"',['/tmp/good.stars'])
                                                                                                                                                                                                                                                                                                 
                #utilities.run('ldacfilter -i ' + base + file + ' -o /tmp/good.colors -t PSSC\
                #            -c "(' + dict['color1'] + '>-900) AND (' + dict['color2'] + '>-900);"',['/tmp/good.colors'])
            
                utilities.run('ldacfilter -i /tmp/good.stars' + ppid  + ' -o /tmp/good.colors' + ppid + ' -t PSSC\
                            -c "(' + dict['color1'] + '>-900) AND (' + dict['color2'] + '>-900);"',['/tmp/good.colors' + ppid])
            
                utilities.run('ldaccalc -i /tmp/good.colors' + ppid + ' -t PSSC -c "(' + dict['filter'] + 'mag - SEx_' + mag + ');"  -k FLOAT -n magdiff "" -o /tmp/all.diff.cat' + ppid,['/tmp/all.diff.cat' + ppid] )
            
                utilities.run('ldactoasc -b -q -i /tmp/all.diff.cat' + ppid + ' -t PSSC -k SEx_' + mag + ' ' + dict['filter'] + 'mag SEx_FLUX_RADIUS SEx_CLASS_STAR ' + dict['filter'] + 'err ' + dict['color1'] + ' > /tmp/mk_sat' + ppid,['/tmp/mk_sat' + ppid] )
            
            
            #    run('ldactoasc -b -q -i ' + base + file + ' -t PSSC -k SEx_' + mag + '_' + filter +  ' ' + dict['filter'] + 'mag SEx_FLUX_RADIUS SEx_CLASS_STAR ' + dict['filter'] + 'err ' + dict['color1'] + ' > /tmp/mk_sat',['/tmp/mk_sat'] )
                                                                                                                                                                                                                                                                                                  
                val = [] 
                #val = raw_input("Look at the saturation plot?")
                if len(val)>0:
                    if val[0] == 'y' or val[0] == 'Y':
                        mk_saturation_plot.mk_saturation('/tmp/mk_sat' + ppid,filter)
                        # make stellar saturation plot                              
            
                lower_mag,upper_mag,lower_diff,upper_diff = re.split('\s+',open('box' + filter,'r').readlines()[0])

                lower_diff = str(0)
                upper_diff = str(10)
                
                utilities.run('ldacfilter -i /tmp/all.diff.cat' + ppid + ' -t PSSC\
                            -c "(((' + dict['filter'] + 'mag>' + lower_mag + ') AND (' + dict['filter'] + 'mag<' + upper_mag + ')) AND (magdiff>' + lower_diff + ')) AND (magdiff<' + upper_diff + ');"\
                            -o /tmp/filt.mag.cat' + ppid ,['/tmp/filt.mag.cat' + ppid])
            
                utilities.run('ldactoasc -b -q -i /tmp/filt.mag.cat' + ppid + ' -t PSSC -k SEx_Xpos_ABS SEx_Ypos_ABS > /tmp/positions' + ppid,['/tmp/positions' + ppid] )
            
                utilities.run('ldacaddkey -i /tmp/filt.mag.cat' + ppid + ' -o /tmp/filt.airmass.cat' + ppid + ' -t PSSC -k AIRMASS 0.0 FLOAT "" ',['/tmp/filt.airmass.cat' + ppid]  )
                
                utilities.run('ldactoasc -b -q -i /tmp/filt.airmass.cat' + ppid + ' -t PSSC -k SEx_' + mag + ' ' + dict['filter'] + 'mag ' + dict['color1'] + ' ' + dict['color2'] + ' AIRMASS SEx_' + magerr + ' ' + dict['filter'] + 'err SEx_Xpos_ABS SEx_Ypos_ABS > /tmp/input.asc' + ppid ,['/tmp/input.asc' + ppid] )
                                                                                                                                                                                                                                                                                                 
                                                                                                                                                                                                                                                                                                 
                #utilities.run('ldactoasc -b -q -i /tmp/filt.airmass.cat -t PSSC -k SEx_' + mag + ' ' + dict['filter'] + 'mag ' + dict['color1'] + ' ' + dict['color2'] + ' AIRMASS SEx_' + magerr + ' ' + dict['filter'] + 'err SEx_Ra SEx_Dec > /tmp/input.asc',['/tmp/input.asc'] )
                    
                # fit photometry
                #utilities.run("./photo_abs_new.py --input=/tmp/input.asc \
                #    --output=/tmp/photo_res --extinction="+str(dict['EXTCOEFF'])+" \
                #    --color="+str(dict['COLCOEFF'])+" --night=-1 --label="+dict['color1']+" --sigmareject=3\
                #     --step=STEP_1 --bandcomp="+dict['filter']+" --color1="+dict['color1']+" --color2="+dict['color2'])
                                                                                                                                                                                                                                                                                                 
                import photo_abs_new                
                
                good_stars = photo_abs_new.run_through('illumination',infile='/tmp/input.asc' + ppid,output='/tmp/photo_res',extcoeff=dict['color1'],sigmareject=3,step='STEP_1',bandcomp=dict['filter'],color1which=dict['color1'],color2which=dict['color2'])
              
                if int(ROTATION) == 0: 
                    stars_0.append(good_stars)

                if int(ROTATION) == 1: 
                    stars_90.append(good_stars)


    from copy import copy
   

    if len(stars_0)> 0:
        dict = copy(stars_0[0])                                                                                                                                                                        
        blank_0 = {} 
        for key in dict.keys():
            blank_0[key] = []
            for i in range(len(stars_0)): 
                for j in range(len(stars_0[i][key])): blank_0[key].append(stars_0[i][key][j]) 
                #print key, blank[key]
                                                                                                                                                                                                       
        photo_abs_new.calcDataIllum('illum',1000, blank_0['corr_data'], blank_0['airmass_good'], blank_0['color1_good'], blank_0['color2_good'], blank_0['magErr_good'], blank_0['X_good'], blank_0['Y_good'],rot=0)


    if len(stars_90)> 0:
        dict = copy(stars_90[0])                                                                                                                                                                              
        blank_90 = {} 
        for key in dict.keys():
            blank_90[key] = []
            for i in range(len(stars_90)): 
                for j in range(len(stars_90[i][key])): blank_90[key].append(stars_90[i][key][j]) 
                #print key, blank[key]                                                                            
                                                                                                                                                                                                              
        photo_abs_new.calcDataIllum('illum',1000, blank_90['corr_data'], blank_90['airmass_good'], blank_90['color1_good'], blank_90['color2_good'], blank_90['magErr_good'], blank_90['X_good'], blank_90['Y_good'],rot=1)


#from config_bonn import cluster
import sys
cluster = sys.argv[1]
filter = 'W-C-RC'

#filters = ['W-J-B','W-J-V','W-C-RC','W-C-IC','W-S-Z+']

filters = ['W-C-RC','W-C-IC','W-S-Z+']
import pickle
for filter in filters:
    if 0:
        import os
        os.system('rm -rf /tmp/*')
        #try: 
        if 1:
            exposures = sextract(filter,cluster)                   
                                                                   
            if len(exposures):
                exposures = match(exposures,cluster)              
                print exposures
                f = open('/tmp/tmppickle' + cluster + filter,'w')
                m = pickle.Pickler(f)
                pickle.dump(exposures,m)
                f.close()
        #except: print 'failed'
    if 1:
        #f = open('/tmp/tmppickle' + cluster + filter,'r')
        #m = pickle.Unpickler(f)
        #exposures = m.load()
        #for key in exposures.keys():
        #    print exposures[key]['matched_cat']
        #print exposures
        from glob import glob
        illum_path='/nfs/slac/g/ki/ki05/anja/SUBARU/ILLUMINATION/%(fil_directory)s/' % {'filter':filter}
        ROTATION = 0
        path = illum_path + '/' + str(ROTATION) + '/*'
        files = glob(path)
        files_there = []
        import os
        for file in files:
            print len(glob(os.readlink(file)))
            print os.readlink(file), file, os.readlink(file) == file
            if len(glob(os.readlink(file))) == 1: # and os.readlink(file) != file:
                files_there.append(file) 
                print files_there
        print len(files)
        print len(files_there)
        phot(files_there,filter,ROTATION)
