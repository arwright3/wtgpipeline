#! /usr/bin/env python
import astropy.io.fits as pyfits
from matplotlib.pyplot import *
from numpy import *
import sys ; sys.path.append('/u/ki/awright/InstallingSoftware/pythons')
from fitter import Gauss
from UsefulTools import names, FromPick_data_true, FromPick_data_spots, GetMiddle, GetSpots_bins_values, ShortFileString, num2str
from collections import Counter
import scipy
import scipy.stats
import pdb
import itertools
import pickle
from imagetools import GetCCD,GetReads,around,points_around,listtuple,totuple,equalequal,splitter,get_center,get_centerY,get_centerX, NthEntry2Pos, HCcorner
from glob import glob
import time
import os
import shutil
#Plotting data
t1=time.time()
tm_year,tm_mon,tm_mday,tm_hour,tm_min,tm_sec,tm_wday, tm_yday,tm_isdst=time.localtime()
DateString=str(tm_mon)+'/'+str(tm_mday)+'/'+str(tm_year)
FileString=ShortFileString(sys.argv[0])
#Preliminaries: import and backup files first
path_to_data=sys.argv[1]+'/'
files=glob(path_to_data+'globalweight_[1-9].fits')+[path_to_data+'globalweight_10.fits']
if not os.path.isdir(path_to_data+'ORIGINAL_globalweights'):
	os.makedirs(path_to_data+'ORIGINAL_globalweights')

for fl in files:
	if not os.path.isfile(path_to_data+'ORIGINAL_globalweights/'+fl):
		shutil.copy(fl,path_to_data+'ORIGINAL_globalweights')
		#if there isn't an original copy the file to the originals dir
	else:
		shutil.copy(path_to_data+'ORIGINAL_globalweights/'+fl,path_to_data)
		#if there is an origonal copy it here so that I'm working with the original file

#Preliminaries: Define necessary functions
uplims,lowlims=zeros((10,4)),zeros((10,4))
#fig_streaks (streaks) and fig_patches (patches) turned off for now
#PlotShow_On_Off={'fig_zoom_corner':0,'fig_corner':0,'fig_streaks':0,'fig_patches':0,'fig_cutgrid':1,'fig_grid':1,'fig_CCD':0,'fig_hist':0}
PlotShow_On_Off={'fig_zoom_corner':1,'fig_corner':1,'fig_streaks':0,'fig_patches':20,'fig_cutgrid':1,'fig_grid':1,'fig_CCD':1,'fig_hist':1}
#fig_corner does fig_corner and fig_zoom_corner
PlotSave_On_Off={'fig_corner':True,'fig_streaks':True,'fig_patches':True}
#$PlotSave_On_Off={'fig_corner':False,'fig_streaks':False,'fig_patches':False}
#use this to save figs after the loop now!
endneeds={'fig_zoom_corner':range(4)}
Nmax=40
Ngsp=0
Ngsp_max=30
#STUFF I WANT OUT OF LOOP
in_func=lambda p: (lambda x: p in x)
#CUT:cut params set here
hist_cut_num=50 #the cutoff point where you say anything bin with this number or less in the histogram is considered a flyer
block_level=50 #<100
patch_level=3 #=3 or 2?
GSpatch_level=7
grid_level=50
#define the "almost" parameters
gridNsigs=5.5
gspNsigs=6
#define the cut parameters
block_highbias=.3 #give it a high bias so that it's easier to find points above average
block_cut=3.5 #3.2
block_highbias=0.3 #0.3
grid_cut=6.0 #6.0
gsp_cut=7.4 #7.4
#ZOOM OUT CUT:cut with higher grid and lower gsp
grid_cut_Zout=8.5
gsp_cut_Zout=7.0
#ZOOM IN CUT: cut with higher gsp and lower grid
gsp_cut_Zin=12.5

#cutdir='Plots_gridcut'+num2str(grid_cut)+'_gspcut'+num2str(gsp_cut)
pltdir=path_to_data+'/Plots_RegionMaker'
if not os.path.isdir(pltdir):
	os.makedirs(pltdir)


#$prompts=['cut figure '+str(i+3)+'? (0=dont cut<1=cut,nan=no idea): ' for i in range(Ngsp_max)]
#$cut_list=range(Ngsp_max)
#$signif_gsp=[]
#$signif_grid=[]

#for fl in files:
for fl in files:
	figlist={'fig_corner':range(4),'fig_zoom_corner':range(4),'fig_cutgrid':range(40),'fig_uncutgrid':range(40),'fig_grid':range(4)}
	Ntimes_uncutgrid,Ntimes_cutgrid=1,1
	print '\n##################'+fl+'#######################\n'
	fitfl=pyfits.open(fl,mode='update')
	start_image=fitfl[0].data
	CCDnum=GetCCD(fl)
	CCDextrema=(start_image[start_image>0.0].min(),start_image.max())
	bins=arange(CCDextrema[0],CCDextrema[1],.01)
	#Get limits one readout at a time
	middle_image=start_image.copy()
	reads1=GetReads(middle_image)
	#plot light histogram showing cuts
	if PlotShow_On_Off['fig_hist']: fig_hist=figure(figsize=(8.5,15));fig_hist.suptitle('fig_hist: CCD # '+str(CCDnum),size=13)
	for rnum,r1 in enumerate(reads1):
		r1[r1==0]=nan
		dummy_r1=r1.copy()
		dummy_r1[dummy_r1==0]=nan
		#STEP1:apply limits to readouts
		x,bins=histogram(dummy_r1.flatten(),bins=linspace(0,2,201)) 
		countup=cumsum(x<hist_cut_num)
		counter=bincount(countup)
		start_spot=sum(counter[:counter.argmax()])+1
		end_spot=sum(counter[:counter.argmax()+1])
		lowlim=bins[start_spot]
		uplim=bins[end_spot]
		outsides=(r1<lowlim)+(r1>uplim)
		#$(Hcorner,Hstring),(Ccorner,Cstring)=HCcorner(r1)
		#STEP2:don't apply limits to corners
		(HXs,HYs),(CXs,CYs)=HCcorner(dummy_r1)
		r1[outsides]=nan
		CornCutr1=r1.copy()
		b4=isnan(CornCutr1)
		r1[HXs[0]:HXs[1],HYs[0]:HYs[1]]=dummy_r1[HXs[0]:HXs[1],HYs[0]:HYs[1]]
		r1[CXs[0]:CXs[1],CYs[0]:CYs[1]]=dummy_r1[CXs[0]:CXs[1],CYs[0]:CYs[1]]
		Nreplaced=sum(b4)-sum(isnan(r1))
		if PlotShow_On_Off['fig_corner']:
			#plot the entire readout with b4 and after corners are put back in
			fig_corner=figure(figsize=(6,15))
			fig_corner.suptitle('fig_corner: '+str(Nreplaced)+' total points put back in\ncircles over points that were put back in\nwhite=hot corner & black=cold corner',size=13)
			ax1=fig_corner.add_subplot(121);imshow(CornCutr1,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left');colorbar();ax1.set_title('cuts applied to corner')
			HXX=(array(HXs)-2076).__abs__().argmin()
			HYY=(array(HYs)-248).__abs__().argmin()
			CXX=(array(CXs)-2076).__abs__().argmin()
			CYY=(array(CYs)-248).__abs__().argmin()
			plot([HYs[0],HYs[1]],[HXs[HXX]]*2,'w');plot([HYs[HYY]]*2,[HXs[0],HXs[1]],'w')
			plot([CYs[0],CYs[1]],[CXs[CXX]]*2,'k');plot([CYs[CYY]]*2,[CXs[0],CXs[1]],'k')
			changed=b4*(logical_not(isnan(r1)))
			changeX,changeY=nonzero(changed)
			scatter(changeY,changeX,marker='o',facecolor='none',edgecolor='k')
			ax2=fig_corner.add_subplot(122);imshow(r1,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left');colorbar();Xlim2=ax2.get_xlim();Ylim2=ax2.get_ylim();ax2.set_title('put corner back in')
			plot([HYs[0],HYs[1]],[HXs[HXX]]*2,'w');plot([HYs[HYY]]*2,[HXs[0],HXs[1]],'w')
			plot([CYs[0],CYs[1]],[CXs[CXX]]*2,'k');plot([CYs[CYY]]*2,[CXs[0],CXs[1]],'k')
			ax2.set_xlim(Xlim2);ax2.set_ylim(Ylim2)
			ax1.set_xlim(Xlim2);ax1.set_ylim(Ylim2)
			scatter(changeY,changeX,marker='o',facecolor='none',edgecolor='k')
			figlist['fig_corner'][rnum]=(fig_corner,pltdir+'/plt_corner'+str(CCDnum)+'_read'+str(rnum))
		if PlotShow_On_Off['fig_zoom_corner']:
			#now show corners zoomed in
			Hchanged=b4[HXs[0]:HXs[1],HYs[0]:HYs[1]]*(logical_not(isnan(r1[HXs[0]:HXs[1],HYs[0]:HYs[1]])))
			HchangeX,HchangeY=nonzero(Hchanged)
			Cchanged=b4[CXs[0]:CXs[1],CYs[0]:CYs[1]]*(logical_not(isnan(r1[CXs[0]:CXs[1],CYs[0]:CYs[1]])))
			CchangeX,CchangeY=nonzero(Cchanged)
			HCornCutr1_area=(CornCutr1[HXs[0]:HXs[1],HYs[0]:HYs[1]]).copy()
			CCornCutr1_area=(CornCutr1[CXs[0]:CXs[1],CYs[0]:CYs[1]]).copy()
			Hr1_area=(r1[HXs[0]:HXs[1],HYs[0]:HYs[1]]).copy()
			Cr1_area=(r1[CXs[0]:CXs[1],CYs[0]:CYs[1]]).copy()
			endneeds['fig_zoom_corner'][rnum]=(Nreplaced,HCornCutr1_area,CCornCutr1_area,Hr1_area,Cr1_area,HXs,HYs,CXs,CYs,HchangeX,HchangeY,CchangeX,CchangeY)
		print 'replaced # corner pixels=',Nreplaced
		uplims[CCDnum-1][rnum]=uplim
		lowlims[CCDnum-1][rnum]=lowlim
		Ncut=sum(isnan(r1))
		CutFrac=Ncut/float(r1.size)
		if PlotShow_On_Off['fig_hist']:
			ax=fig_hist.add_subplot(2,2,rnum+1)
			x,bins,patch=ax.hist(dummy_r1.flatten(),bins=linspace(0,2,201),log=True) 
			ax.plot([lowlim,lowlim],[1,max(x)],'r')
			ax.plot([uplim,uplim],[1,max(x)],'r')
			ax.set_xlim(CCDextrema[0]-.01,CCDextrema[1]+.01)
			ax.set_ylim(1,10**7)
			ax.text(ax.get_xlim()[0],10**6.3,'%cut='+str(round(100*CutFrac,7)))
			ax.set_title('Readout #'+str(rnum+1)+'\nLow Lim: '+str(round(lowlim,2))+'\nUp Lim: '+str(round(uplim,2)))
	if PlotShow_On_Off['fig_hist']:
		NameString=(pltdir+'/plt_hist'+str(CCDnum))
		fig_hist.text(.03,.03,"File:"+os.getcwd()+fl,size=10)
		fig_hist.text(.303,.013,"Date:"+DateString,size=10)
		fig_hist.text(.503,.013,"Named:"+NameString,size=10)
		fig_hist.savefig(NameString)
	final_image=middle_image.copy()
	reads2=GetReads(final_image)
	for rnum,r2 in enumerate(reads2):
		print "step #"+str(rnum)+":  nansum(final_image)=",nansum(final_image)
		bads=asarray(nonzero(isnan(r2))).T
		#STEP3:don't go along streaks (find spots along streaks not at the top and bottom and remove them from bads)
		x,bins=histogram(bads[:,1],bins=arange(513)-.5)
		rmXbads=nonzero(x>4100)[0]
		for rmX in rmXbads:
			keep_col=bads[:,1]!=rmX
			bads=bads[keep_col]
		rm_middle=nonzero((x>100)*(x<4101))[0]
		thespots=[]
		for rmX in rm_middle:
			good_cols=bads[bads[:,1]!=rmX]
			bad_cols=bads[bads[:,1]==rmX]
			indicies=bad_cols[:,0]
			splits=array_split(indicies,where(diff(indicies)!=1)[0]+1)
			lengths=array([len(split) for split in splits])
			jump=lengths.max()
			if jump>50:
				jumparg=lengths.argmax()
				pickfrom=cumsum(append([0],lengths))
				x1=pickfrom[jumparg]
				x2=x1+jump-1
			else:continue
			thespots+=[bad_cols[x1],bad_cols[x2]]
			top_bottom=asarray([bad_cols[x1],bad_cols[x2]])
			new_bads=append(good_cols,top_bottom)
			bads=new_bads.reshape(good_cols.shape[0]+2,good_cols.shape[1])
		#PLOTstreaks
		if thespots and PlotShow_On_Off['fig_streaks']:
			thespots=array(thespots)
			fig_streaks=figure();imshow(r2,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left');fig_streaks.suptitle('fig_streaks: streaks found and shown here',size=13)
			scatter(thespots[:,1],thespots[:,0])
			if PlotSave_On_Off['fig_streaks']:
				fig_streaks.savefig(pltdir+'/plt_streaks'+str(CCDnum)+'_read'+str(rnum))
		#make list "others" for bads that need to be searched around and "around_bads" for spots within the patch around bad that should be excluded from the grid search in STEP4
		others=[]
		around_bads=[]
		for bad in bads:
			if not (((bads==[bad[0]-1,bad[1]]).prod(axis=1).any()) and ((bads==[bad[0],bad[1]-1]).prod(axis=1).any()) and ((bads==[bad[0]+1,bad[1]]).prod(axis=1).any()) and ((bads==[bad[0],bad[1]+1]).prod(axis=1).any())):
				others.append(tuple(bad))
				around_bads+=points_around(r2.shape,bad,level=patch_level)
		#STEP4:grid search for outliers and put them in bads
		#set up grid to search on
		grid_x=[grid_level/2+grid_level*i for i in range(r2.shape[0]/grid_level)]
		grid_y=[grid_level/2+grid_level*i for i in range(r2.shape[1]/grid_level)]
		if grid_y[-1]+grid_level<r2.shape[1]:
			grid_y.append(grid_level/2+grid_level*len(grid_y))
		if grid_x[-1]+grid_level<r2.shape[1]:
			grid_x.append(grid_level/2+grid_level*len(grid_x))
		#plot the readout with circles and boxes around points considered
		if PlotShow_On_Off['fig_grid']:
			fig_grid=figure(figsize=(8.5,15))
			fig_grid.subplots_adjust(bottom=.06,top=.94,right=1,left=0,wspace=0)
			fig_grid.suptitle('fig_grid: reads b4 & after grid search for grid_cut='+str(grid_cut)+' gsp_cut='+str(gsp_cut),size=13)
			fig_grid.text(.03,.02,"File:"+os.getcwd()+'/'+fl,size=10)
			B4ax=fig_grid.add_subplot(1,2,1)
			B4ax.set_title('Before')
			B4ax.imshow(copy(r2),vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			Aax=fig_grid.add_subplot(1,2,2)
			Aax.set_title('After')
			Aax.imshow(r2,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			Gxlims,Gylims=B4ax.get_xlim(),B4ax.get_ylim()
		#PLOTgsp1/4
		if PlotShow_On_Off['fig_cutgrid']:
			Ncounter_cutgrid,Ncounter_uncutgrid=1,1
			fig_cutgrid=figure(figsize=(20,15))
			#fig_cutgrid.set_facecolor('k')
			fig_cutgrid.suptitle('fig_cutgrid: cut for grid_cut='+str(grid_cut)+' gsp_cut='+str(gsp_cut),size=15)
			fig_cutgrid.subplots_adjust(right=.9,top=.95,left=.01,bottom=.05,wspace=.01,hspace=.01)
			fig_cutgrid.text(.03,.02,"File:"+os.getcwd()+'/'+fl,size=10)
			fig_uncutgrid=figure(figsize=(10,15))
			#fig_uncutgrid.set_facecolor('k')
			fig_uncutgrid.suptitle('fig_uncutgrid: UNCUT for grid_cut='+str(grid_cut)+' gsp_cut='+str(gsp_cut),size=15)
			fig_uncutgrid.subplots_adjust(right=.99,top=.95,left=.01,bottom=.05,wspace=.01,hspace=.01)
			fig_uncutgrid.text(.03,.02,"File:"+os.getcwd()+'/'+fl,size=10)
		#$pairspots,cutpairspots,unpairspots=[],[],[]`
		pts_covered=set()
		for xx,yy in itertools.product(grid_x,grid_y):
			(grid,grid_pts)=around(r2,(xx,yy),grid_level)
			#remember grid_pts are points for r, not for grid
			Nums,bins=histogram(grid.flatten(),bins=linspace(0.25,1.75,601))
			fitinst=Gauss(GetMiddle(bins),Nums,threshold=.0002)
			GSsigma=fitinst.sigma
			GSmean=fitinst.mean
			#later: I treat it equal for points above average and below, might want to have a high bias for selection as well as cut
			grid_signifs=(grid-GSmean).__abs__()/GSsigma
			GSflyers=grid_signifs>gridNsigs
			lowerleft=grid_pts[:,0]
			GSpairs=asarray(nonzero(GSflyers)).T+lowerleft
			pts_i=[tuple(uu) for uu in GSpairs if tuple(uu) not in around_bads]
			Rpts=[points_around(r2.shape,pairpair,patch_level) for pairpair in pts_i]
			pts_f=set()
			#if there are mutiple points in GSpairs that are within the same patch, then pick out the most significant point and only use that one
			for qq in pts_i:
				qq_in=in_func(qq)
				#T/F if qq in R(p) for all p in pts_i
				pts_has_qq_in_Rpt=map(qq_in,Rpts)
				#significance of all p in R(qq), if p !in R(qq), it's 0
				signifs_in_Rqq=array([abs(r2[pts_i[i]]-GSmean) if ptTF else 0 for i,ptTF in enumerate(pts_has_qq_in_Rpt)])
				pts_f.add(pts_i[signifs_in_Rqq.argmax()])
			pts_f-=pts_covered
			pts_covered|=pts_f
			#now loop over the bad points in this portion of the grid search and see if they are really bad
			for pairpair in pts_f:
				(GSpatch,GSpatch_pts)=around(r2,pairpair,GSpatch_level)
				gsp=GSpatch[isfinite(GSpatch)]
				Nums,bins=histogram(gsp,bins=linspace(0.25,1.75,601))
				fitinst=Gauss(GetMiddle(bins),Nums,threshold=.001)
				gspsigma=fitinst.sigma
				gspmean=fitinst.mean
				significance_grid=abs(r2[pairpair]-GSmean)/GSsigma
				significance_gsp=abs(r2[pairpair]-gspmean)/gspsigma
				CUTtight= (significance_grid>grid_cut) * (significance_gsp>gsp_cut)
				#later: might want to add different conditions onto tightcut specific to certain defects in the image
				CUTZin= (significance_gsp>gsp_cut_Zin)
				CUTZout= (significance_gsp>gsp_cut_Zout)*(significance_grid>grid_cut_Zout)
				CUTloose= significance_gsp>gspNsigs
				CUTall=CUTtight+CUTZin+CUTZout
				if CUTall:
					if PlotShow_On_Off['fig_grid']:
						B4ax.plot([grid_pts[1,0],grid_pts[1,0],grid_pts[1,1],grid_pts[1,1],grid_pts[1,0]],[grid_pts[0,0],grid_pts[0,1],grid_pts[0,1],grid_pts[0,0],grid_pts[0,0]],'k-')
						Aax.plot([grid_pts[1,0],grid_pts[1,0],grid_pts[1,1],grid_pts[1,1],grid_pts[1,0]],[grid_pts[0,0],grid_pts[0,1],grid_pts[0,1],grid_pts[0,0],grid_pts[0,0]],'k-')
						B4ax.scatter(pairpair[1],pairpair[0],c='k',marker='o',facecolor='none')
						Aax.scatter(pairpair[1],pairpair[0],c='k',marker='o',facecolor='none')
						#$B4ax.text(pairpair[1],pairpair[0]+.5,str(round(significance_grid,2)))
						#$B4ax.text(pairpair[1],pairpair[0]-.5,str(round(significance_gsp,2)),color='purple')
					if PlotShow_On_Off['fig_cutgrid']:
						#PLOTgsp2/4
						if (Ncounter_cutgrid==Nmax):
							Ncounter_cutgrid=1
							figlist['fig_cutgrid'][Ntimes_cutgrid]=(fig_cutgrid,pltdir+'/plt_cutgrid'+str(CCDnum)+'_gridcut'+num2str(grid_cut)+'_gspcut'+num2str(gsp_cut)+'_num'+str(Ntimes_cutgrid))
							fig_cutgrid=figure(figsize=(20,15))
							#fig_cutgrid.set_facecolor('k')
							fig_cutgrid.suptitle('fig_cutgrid: cut for grid_cut='+str(grid_cut)+' gsp_cut='+str(gsp_cut),size=15)
							#$fig_cutgrid.subplots_adjust(right=.9,top=.95,left=.01,bottom=.05,wspace=.01,hspace=.01)
							fig_cutgrid.subplots_adjust(right=.99,top=.95,left=.01,bottom=.05,wspace=.01,hspace=.01)
							fig_cutgrid.text(.03,.02,"File:"+os.getcwd()+'/'+fl,size=10)
							Ntimes_cutgrid+=1
						#put area around here in the cut plot
						#$cutpairspots+=points_around(r2.shape,pairpair,GSpatch_level)
						cutAX=fig_cutgrid.add_subplot(8,10,Ncounter_cutgrid)
						cutAX.set_xticklabels([]);cutAX.set_yticklabels([]);cutAX.set_xticks([]);cutAX.set_yticks([])
						cutAX.imshow(GSpatch.copy(),vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')		
						cutAX.text(8,8,str(round(significance_grid,2)))
						cutAX.text(8,6,str(round(significance_gsp,2)),color='purple')
						scatpt=array(pairpair)-GSpatch_pts[:,0]
						cutAX.scatter(scatpt[1],scatpt[0],color='w',facecolor='none',s=3)
						cutAX.set_xlim(0,14);cutAX.set_ylim(1,13)
						if not CUTtight:
							if CUTZin:
								cutAX.text(5,10,'CUTZin')
							if CUTZout:
								cutAX.text(5,10,'CUTZout')
						cutAX=fig_cutgrid.add_subplot(8,10,Ncounter_cutgrid+40)
						cutAX.set_xticklabels([]);cutAX.set_yticklabels([]);cutAX.set_xticks([]);cutAX.set_yticks([])
						im_cutgrid=cutAX.imshow(GSpatch,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')		
						cutAX.set_xticklabels([]);cutAX.set_yticklabels([]);cutAX.set_xticks([]);cutAX.set_yticks([])
						cutAX.text(8,8,str(round(significance_grid,2)))
						cutAX.text(8,6,str(round(significance_gsp,2)),color='purple')
						scatpt=array(pairpair)-GSpatch_pts[:,0]
						cutAX.scatter(scatpt[1],scatpt[0],color='w',facecolor='none',s=3)
						cutAX.set_xlim(0,14);cutAX.set_ylim(1,13)
						if not CUTtight:
							if CUTZin:
								cutAX.text(5,10,'CUTZin')
							if CUTZout:
								cutAX.text(5,10,'CUTZout')
						#changed:if pt to be cut, then put all of R(p) besides the outer layer in covered points
						pts_covered|=set(points_around(r2.shape,pairpair,patch_level-1))
						Ncounter_cutgrid+=1
					#end of "if CUTtight": apply the cut
					others.append(pairpair)
				elif CUTloose and PlotShow_On_Off['fig_cutgrid']: 
					#PLOTgsp3/4
					if (Ncounter_uncutgrid==Nmax):
						Ncounter_uncutgrid=1
						figlist['fig_uncutgrid'][Ntimes_uncutgrid]=(fig_uncutgrid,pltdir+'/plt_uncutgrid'+str(CCDnum)+'_gridcut'+num2str(grid_cut)+'_gspcut'+num2str(gsp_cut)+'_num'+str(Ntimes_cutgrid))
						fig_uncutgrid=figure(figsize=(10,15))
						#fig_uncutgrid.set_facecolor('k')
						fig_uncutgrid.suptitle('fig_uncutgrid: UNCUT for grid_cut='+num2str(grid_cut)+' gsp_cut='+num2str(gsp_cut),size=15)
						fig_uncutgrid.subplots_adjust(right=.99,top=.95,left=.01,bottom=.05,wspace=.01,hspace=.01)
						fig_uncutgrid.text(.03,.02,"File:"+os.getcwd()+'/'+fl,size=10)
						Ntimes_uncutgrid+=1
					#if it's not cut by grid or gsp and it satisfies the loose cut and Plot is on
					#then put in uncut plot
					#$and this spot hasen't been plotted b4
					#$unpairspots+=points_around(r2.shape,pairpair,GSpatch_level)
					uncutAX=fig_uncutgrid.add_subplot(8,5,Ncounter_uncutgrid)
					uncutAX.set_xticklabels([]);uncutAX.set_yticklabels([]);uncutAX.set_xticks([]);uncutAX.set_yticks([])
					uncutAX.imshow(GSpatch,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')		
					uncutAX.text(8,8,str(round(significance_grid,2)))
					uncutAX.text(8,6,str(round(significance_gsp,2)),color='purple')
					scatpt=array(pairpair)-GSpatch_pts[:,0]
					uncutAX.scatter(scatpt[1],scatpt[0],color='w',facecolor='none',s=3)
					uncutAX.set_xlim(0,14);uncutAX.set_ylim(1,13)
					Ncounter_uncutgrid+=1
				#$old way of trying to optimize cut params
				#$if Ngsp<Ngsp_max and (pairpair not in pairspots):
				#$	pairspots+=points_around(r2.shape,pairpair,GSpatch_level)
				#$	fig_gsp=figure(figsize=(8,15));ax_gsp=fig_gsp.add_subplot(211)
				#$	if abs(significance_gsp)<abs(significance_grid):
				#$		fig_gsp.suptitle('less important upon zooming')
				#$	else:
				#$		fig_gsp.suptitle('ZOOM IN makes more important')
				#$	ax_gsp.set_title(str(round(significance_gsp,2)))
				#$	ax_gsp.imshow(GSpatch,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
				#$	ax_gsp.text(8,7.5,str(round(significance_grid,2)))
				#$	ax_gsp.text(8,6.5,str(round(significance_gsp,2)),color='purple')
				#$	ax_grid=fig_gsp.add_subplot(212)
				#$	ax_grid.set_title(str(round(significance_grid,2)))
				#$	ax_grid.imshow(grid,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
				#$	signif_gsp.append(round(significance_gsp,2))
				#$	signif_grid.append(round(significance_grid,2))
				#$	cut_list[Ngsp]=raw_input(prompts[Ngsp])
				#$	Ngsp+=1 
		#put circles over the points and write the significance of the point 
		if PlotShow_On_Off['fig_grid']:
			B4ax.set_xlim(Gxlims);B4ax.set_ylim(Gylims)
			Aax.set_xlim(Gxlims);Aax.set_ylim(Gylims)
			figlist['fig_grid'][rnum]=(fig_grid,pltdir+'/plt_grid'+str(CCDnum)+'_read'+str(rnum)+'_ReadoutGridCuts_gridcut'+num2str(grid_cut)+'_gspcut'+num2str(gsp_cut))
		plot_coverage=set()
		#STEP5:search around nans+flyers-streaks for bad values and set=nan
		for bnum,bad in enumerate(others):
			#remember#  array(X,Y)=====plot(Y,X)  #for axes defined by imshow(origin='lower left')
			(block,block_pts),(patch,patch_pts)=around(r2,bad,[block_level,patch_level])
			flat_block=(block.flatten()).copy()
			flat_block=flat_block[isfinite(flat_block)]
			#use sigma rather than blockhigh blocklow and block_cut
			Nums,bins=histogram(flat_block,bins=linspace(0.25,1.75,601))
			fitinst=Gauss(GetMiddle(bins),Nums,threshold=.0002)
			light_sigma=fitinst.sigma
			light_mean=fitinst.mean
			blocklow=light_mean-(light_sigma*block_cut)
			blockhigh=light_mean+(light_sigma*(block_cut-block_highbias))
			outsides=(patch>blockhigh)+(patch<blocklow)
			p=patch.copy();b=block.copy()
			patch[outsides]=nan
			lowerleft=patch_pts[:,0]
			covered_spots=totuple(asarray(nonzero(outsides)).T+lowerleft)
			#see if there is a spot surrounded by nans that isn't nan
			nanspots=isnan(patch)
			for i,j in itertools.product(range(1,patch.shape[0]-1),range(1,patch.shape[1]-1)):
				if not nanspots[i,j]:
					#if the spot to the left and right or above and below are nan, make it nan
					if nanspots[i+1,j]*nanspots[i-1,j]:
						patch[i,j]=nan
					if nanspots[i,j+1]*nanspots[i,j-1]:
						patch[i,j]=nan
					#if 3 spots corner surrounding it are nan, make it nan
					if nanspots[i+1,j]*nanspots[i+1,j+1]*nanspots[i,j+1]: #upper right
						patch[i,j]=nan
					if nanspots[i-1,j]*nanspots[i-1,j+1]*nanspots[i,j+1]: #upper left
						patch[i,j]=nan
					if nanspots[i+1,j]*nanspots[i+1,j-1]*nanspots[i,j-1]: #lower right
						patch[i,j]=nan
					if nanspots[i-1,j]*nanspots[i-1,j-1]*nanspots[i,j-1]: #lower left
						patch[i,j]=nan
			if (bnum>=PlotShow_On_Off['fig_patches']) or (bad in plot_coverage):
				continue
			for i,j in itertools.product(range(patch.shape[0]),range(patch.shape[1])):
				plot_coverage.add((lowerleft[0]+i,lowerleft[1]+j))
			fig_patches=figure(figsize=(20,15))
			ax=fig_patches.add_subplot(241)
			im=ax.imshow(r2,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			xlims,ylims=ax.get_xlim(),ax.get_ylim()
			ax.plot([patch_pts[1,0],patch_pts[1,0],patch_pts[1,1],patch_pts[1,1],patch_pts[1,0]],[patch_pts[0,0],patch_pts[0,1],patch_pts[0,1],patch_pts[0,0],patch_pts[0,0]],'r')
			ax.plot([block_pts[1,0],block_pts[1,0],block_pts[1,1],block_pts[1,1],block_pts[1,0]],[block_pts[0,0],block_pts[0,1],block_pts[0,1],block_pts[0,0],block_pts[0,0]],'k-')
			for spot in covered_spots:
				scatter(spot[1],spot[0],c='k',marker='o',facecolor='none')
			ax.set_xlim(xlims),ax.set_ylim(ylims)
			ax.set_xticklabels([])
			fig_patches.add_subplot(242)
			imshow(b,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			fig_patches.add_subplot(245)
			imshow(p,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			fig_patches.add_subplot(246)
			imshow(patch,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			ax_patch=fig_patches.add_subplot(122)
			Nums,bins,patch=hist(flat_block,bins=linspace(0.25,1.75,601),log=True)
			xx,yy=fitinst.getfitline()
			yylims=ax_patch.get_ylim()
			plot(xx,yy,'green')
			plot([blocklow,blocklow],yylims,'r--')
			plot([blockhigh,blockhigh],yylims,'r--')
			ax_patch.set_ylim(yylims);ax_patch.set_xlim(CCDextrema[0]-.01,CCDextrema[1]+.01)
			fig_patches.colorbar(im)
			if PlotSave_On_Off['fig_patches']:
				if not outsides.any():
					fig_patches.savefig(pltdir+'/plt_patches'+str(CCDnum)+'_read'+str(rnum)+'_none_blockcuthigh'+num2str(block_cut)+'_low'+num2str(block_cut-block_highbias)+'_badspot'+str(bad[0])+'_'+str(bad[1]))
				else:
					fig_patches.savefig(pltdir+'/plt_patches'+str(CCDnum)+'_read'+str(rnum)+'_some_blockcuthigh'+num2str(block_cut)+'_low'+num2str(block_cut-block_highbias)+'_badspot'+str(bad[0])+'_'+str(bad[1]))
		#bad loop end
		if PlotShow_On_Off['fig_cutgrid']: 
			#PLOTgsp4/4
			figlist['fig_cutgrid'][Ntimes_cutgrid]=(fig_cutgrid,pltdir+'/plt_cutgrid'+str(CCDnum)+'_gridcut'+num2str(grid_cut)+'_gspcut'+num2str(gsp_cut)+'_num'+str(Ntimes_cutgrid))
			figlist['fig_uncutgrid'][Ntimes_uncutgrid]=(fig_uncutgrid,pltdir+'/plt_uncutgrid'+str(CCDnum)+'_gridcut'+num2str(grid_cut)+'_gspcut'+num2str(gsp_cut)+'_num'+str(Ntimes_cutgrid))
			Ntimes_uncutgrid+=1
			Ntimes_cutgrid+=1
		if PlotShow_On_Off['fig_zoom_corner']:
			Nreplaced,HCornCutr1_area,CCornCutr1_area,Hr1_area,Cr1_area,HXs,HYs,CXs,CYs,HchangeX,HchangeY,CchangeX,CchangeY=endneeds['fig_zoom_corner'][rnum]
			fig_zoom_corner=figure(figsize=(20,10))
			fig_zoom_corner.suptitle('fig_zoom_corner: '+str(Nreplaced)+' total points put back in to the image',size=13)
			ax1=fig_zoom_corner.add_subplot(231)
			ax1.set_title('cuts applied to hot corner')
			ax1.imshow(HCornCutr1_area,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			ax1.scatter(HchangeY,HchangeX,marker='o',facecolor='none',edgecolor='k',s=25)
			ax2=fig_zoom_corner.add_subplot(232)
			ax2.set_title('without cuts in hot corner')
			ax2.imshow(Hr1_area,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			ax2.scatter(HchangeY,HchangeX,marker='o',facecolor='none',edgecolor='k',s=25)
			ax5=fig_zoom_corner.add_subplot(233)
			ax5.set_title('final hot corner')
			ax5.imshow(r2[HXs[0]:HXs[1],HYs[0]:HYs[1]],vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			ax5.scatter(HchangeY,HchangeX,marker='o',facecolor='none',edgecolor='k',s=25)
			ax3=fig_zoom_corner.add_subplot(234)
			ax3.set_title('cuts applied to cold corner')
			ax3.imshow(CCornCutr1_area,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			ax3.scatter(CchangeY,CchangeX,marker='o',facecolor='none',edgecolor='k',s=25)
			ax4=fig_zoom_corner.add_subplot(235)
			ax4.set_title('without cuts in cold corner')
			ax4.imshow(Cr1_area,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			ax4.scatter(CchangeY,CchangeX,marker='o',facecolor='none',edgecolor='k',s=25)
			ax6=fig_zoom_corner.add_subplot(236)
			ax6.set_title('final cold corner')
			ax6.imshow(r2[CXs[0]:CXs[1],CYs[0]:CYs[1]],vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
			ax6.scatter(CchangeY,CchangeX,marker='o',facecolor='none',edgecolor='k',s=25)
			ax1.set_xlim(0,200);ax1.set_ylim(0,200);ax2.set_xlim(0,200);ax2.set_ylim(0,200);ax3.set_xlim(0,200);ax3.set_ylim(0,200);ax4.set_xlim(0,200);ax4.set_ylim(0,200);ax5.set_xlim(0,200);ax5.set_ylim(0,200);ax6.set_xlim(0,200);ax6.set_ylim(0,200)
			figlist['fig_zoom_corner'][rnum]=(fig_zoom_corner,pltdir+'/plt_zoom_corner'+str(CCDnum)+'_read'+str(rnum))
		#read loop end
	#file loop end
	plt_start_image=start_image.copy()
	plt_start_image[start_image==0]=nan
	if PlotShow_On_Off['fig_CCD']:
		fig_CCD=figure(figsize=(20,12))
		fig_CCD.subplots_adjust(left=.05,right=.9)
		fig_CCD.suptitle('fig_CCD: CCD # '+str(CCDnum),size=15)
		ax=fig_CCD.add_subplot(1,3,1)
		ax.set_title('Before: fraction cut='+str(round(sum(isnan(plt_start_image))/float(start_image.size),7))+'\n'+str(isnan(plt_start_image).sum())+' total pixels cut ')
		imshow(plt_start_image,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
		ax=fig_CCD.add_subplot(1,3,2)
		ax.set_title('Middle: fraction cut='+str(round(sum(isnan(middle_image))/float(middle_image.size),7))+'\n'+str(isnan(middle_image).sum())+' total pixels cut ')
		imshow(middle_image,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
		ax=fig_CCD.add_subplot(1,3,3)
		ax.set_title('Final: fraction cut='+str(round(isnan(final_image).sum()/float(final_image.size),7))+'\n'+str(isnan(final_image).sum())+' total pixels cut ')
		im=ax.imshow(final_image,vmin=CCDextrema[0],vmax=CCDextrema[1],interpolation='nearest',origin='lower left')
		ax_final=fig_CCD.add_axes([.92,.15,.03,.7])
		fig_CCD.colorbar(im,cax=ax_final)
		NameString=(pltdir+'/plt_CCD'+str(CCDnum)+'_3LightHist')
		fig_CCD.text(.03,.03,"File:"+os.getcwd()+'/'+fl,size=10)
		fig_CCD.text(.603,.03,"Date:"+DateString,size=10)
		fig_CCD.text(.803,.03,"Named:"+NameString,size=10)
		fig_CCD.savefig(NameString)
	saved_image=final_image.copy()
	saved_image[isnan(saved_image)]=0
	fitfl[0].data=saved_image 
	fitfl.flush()
	#now save the figures I've waited until now to save (so that the final image will be in there)
	for key in figlist.keys():
		try:
			if not PlotShow_On_Off[key]: continue
		except KeyError:
			pass
		for something in figlist[key]:
			if type(something)==int:continue
			else:
				#$if key=='fig_cutgrid':
				#$	ax_cutgrid=something[0].add_axes([.92,.15,.03,.7])
				#$	something[0].colorbar(im_cutgrid,cax=ax_cutgrid)
				something[0].savefig(something[1])
				something[0].clf()
        if PlotShow_On_Off['fig_hist']:
		fig_hist.clf()
	if PlotShow_On_Off['fig_CCD']:
		fig_CCD.clf()
	if PlotShow_On_Off['fig_streaks']:
		fig_streaks.clf()
	if PlotShow_On_Off['fig_patches']:
		fig_patches.clf()

t2=time.time()
print "took ",(t2-t1)/3600.0," hours" 
