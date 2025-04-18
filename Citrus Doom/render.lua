m=math
mx=m.max
mn=m.min
absFunc=m.abs
flr=m.floor
sqrt=m.sqrt
gN=input.getNumber
gB=input.getBool
pi=m.pi
falseVar=false
trueVar=true

function cross(a,b)return a[1]*b[2]-a[2]*b[1]end
function sub(a,b)return{(a[1]-b[1]),(a[2]-b[2])}end
function wrap(a)return ((a+180)%360)-180 end
function cos(a)return m.cos(a/180*pi)end
function tan(a)return m.tan(a/180*pi)end
function at2(a)return m.atan(a[2],a[1])*180/pi end
function clmp(a,b,cr)return mn(mx(b,a),cr)end
function rnd(a)return flr(a+0.5)end
function dist(a,b)return sqrt(((a[1]-b[1])^2)+((a[2]-b[2])^2))end
function rnd2(a)
	a=a-1
	a=a|(a>>1)
	a=a|(a>>2)
	a=a|(a>>4)
	return a+1
end

M={}
romCr=1
levelCr=3
loaded=falseVar
init=trueVar

pp={{0,0},0,0}

wdth=288
wdthH=wdth//2
hght=128
hghtH=hght//2
thngs={}
LOD=400-- higher is more quality
health=100
mRandom=0
transferCache={}
bigNumb=32768
difficulty=3002
fuzz=0
screenBrightTimer=0

tick=0

pixelAspectCorrection=1.2
fov=52
fovT=tan(fov)
vMult=hghtH*pixelAspectCorrection*wdth/hght/fovT

stg=1

xAng={}
for i=-wdthH,wdthH do xAng[i]=at2({1,i/wdthH*fovT})end

function treeing(i)
	if i<bigNumb then
		local g,si=M[7][i]
		si=0<cross({g[3],g[4]},sub(pp[1],g))and 8 or 7
		treeing(g[si])
		treeing(g[15-si])
	else
		ssecs[#ssecs+1]=i-bigNumb
	end
end

function findMe(i,a)
	if i<bigNumb then
		g=M[7][i]
		return findMe(g[0<cross({g[3],g[4]},sub(a,g))and 8 or 7],a)
	else
		return i-bigNumb
	end
end

function findSec(a)
	g=M[5][M[6][a][2]]
	return M[3][M[2][g[4]][g[5]+6]][6]
end

function onTick()
	mN=0

	for j=1,3 do
		if gB(9) and (not loaded)or not M[21]then
			rom=property.getText(romCr.."")
			if rom~="" then
				i=1
				nm=""
				cr=string.sub(rom,i,i)
				while cr~=""or nm~=""do
					if cr==","or cr==""then
						nm=nm+0

						if stg==1 then
							crI=nm
							if M[nm]==nil then
								M[nm]={}
							end
							stg=2
						elseif stg==2 then
							l=nm
							crL=0
							stg=3
						elseif stg==3 then
							cnt=nm
							stg=4
						else
							if crL==0 then
								crL=l
								cnt=cnt-1
								crM={}
								M[crI][#M[crI]+1]=crM
							end
							crM[#crM+1]=nm
							crL=crL-1
							if mx(crL,cnt)==0 then
								stg=1
							end
						end

						nm=""
					else
						nm=nm.. cr
					end
					i=i+1
					cr=string.sub(rom,i,i)
				end

				romCr=romCr+1
			else
				loaded=trueVar
			end
		end
	end

	if loaded then
		init=init or gB(2)
		
		

		
		if health>0 and not init then
			tmp={}
			transferCache[#transferCache+1]=tmp
			rIn=5
			cr=gN(rIn)
			while cr~=0 do
				info={}
				tmp[#tmp+1]=info
				for i=0,8 do
					info[i+1]=gN(rIn+i)
				end
				rIn=rIn+9
				cr=gN(rIn)
			end
		end
		
		if gB(1) then
			switchedSwitch=0
			weapon=gN(1)
			health=gN(3)
			tick=tick+1
			if init then
				for i=1,10 do
					M[i]=M[i+10*levelCr]
				end
				levelCr=levelCr+1
			end
			if gN(2)>0 then
				cr=M[2][gN(2)]
				if cr then
					if cr[4]>3004 then
						LOD=mx(LOD+3*(cr[4]-3006),1)
					elseif cr[4]>3000 then
						difficulty=cr[4]
					end
					switchedSwitch=gN(2)
				end
			end
			
			if gB(3) and weapon~=1 and weapon~=3 then
				screenBrightOffset=0.1
				screenBrightTimer=weapon==5 and 5 or 3
			else
				screenBrightTimer=screenBrightTimer-1
				if screenBrightTimer<1then
					screenBrightOffset=0
				end
			end
			
			for i=1,#transferCache do
				tmp=transferCache[i]
				for j=1,#tmp do
					info=tmp[j]
					cr=info[1]
					if cr>(2^15) then
						cr=M[8][cr-(2^15)]
						cr[1]=info[2]
						cr[2]=info[3]
					elseif cr<0 then
						while -cr>#M[1] do
							M[1][#M[1]+1]=falseVar
						end
						table.remove(M[1],-cr)
					else
						if not M[1][cr] then
							M[1][cr]={}
						end
						cr=M[1][cr]
						for k=1,8 do
							cr[M[19][1][k]]=info[k+1]-- M[19][1] is 1,2,9,6,11,12,19,3
						end
						cr[15]=0
						cr[7]=findMe(#M[7],cr)
						cr[8]=findSec(cr[7])
					end
				end
			end
			transferCache={}
		
			for i=1,#M[6]do
				thngs[i]={}
			end
			for i=1,#M[1] do
				cr=M[1][i]
				
				if cr then
					if init then
						cr[7]=findMe(#M[7],cr)
						cr[8]=findSec(cr[7])
						cr[9]=M[8][cr[8]][1]
						cr[11]=0
						cr[12]=0
						cr[15]=0
						cr[19]=0
						if cr[4]==1 then
							pIn=i
						end
					end
					crMx=0
					for j,v in ipairs({1,2,9}) do
						cr[v]=cr[v]+cr[v+10]
						crMx=crMx+cr[v+10]
					end
					if crMx~=0then-- it is very, very unlikely for an object to be moving but have 0 velocity when measured this way
						cr[7]=findMe(#M[7],cr)
						cr[8]=findSec(cr[7])
					end
					
					cr[15]=cr[15]+1
					cr[20]=dist(cr,pp[1])
					state=M[16][cr[6]]
					if state~=nil then
						if cr[15]>=state[2] and state[2]~=-1 then
							cr[6]=state[4]
							cr[15]=0
						end
					end
					thngs[cr[7]][#thngs[cr[7]]+1]=i
				end
				
			end
			
			
			init=falseVar

			
			cr=M[1][pIn]
			pp[1]={cr[1],cr[2]}
			pp[2]=cr[9]+41
			pp[3]=cr[3]
			

			ssecs={}
			
			treeing(#M[7])

			dpth={}
			walls={}
			vises={}
			clH={}
			flH={}
			thngsOrd={}
			lnLft=wdth
			for i=0,wdth-1 do
				dpth[i],clH[i],flH[i]=#M[6]+2,hghtH+1,-hghtH
			end

			i=1
			while i<=#ssecs and lnLft>0 do
				cr=M[6][ssecs[i]]
				vises[i]={}
				walls[i]={}
				thngsOrd[i]=thngs[ssecs[i]]
				table.sort(thngsOrd[i],function(a,b)return M[1][a][20]>M[1][b][20]end)
				

				for j=cr[2],cr[1]+cr[2]-1 do
					seg=M[5][j]
					line=M[2][seg[4]]

					p1,p2=M[4][seg[1]],M[4][seg[2]]
					pl1,pl2=sub(p1,pp[1]),sub(p2,pp[1])
					ga1=at2(pl1)
					a1,a2=wrap(ga1-pp[3]),wrap(at2(pl2)-pp[3])

					if absFunc(a1)<90 or absFunc(a2)<90 then
						a3,a4=clmp(a1,-fov,fov),clmp(a2,-fov,fov)
						if absFunc(a1)>=90 or absFunc(a2)>=90 then
							prod=cross(pl1,pl2)
							if absFunc(a1)>=90 then
								if prod>0 then a3=-fov else a3=fov end
							else
								if prod<0 then a4=-fov else a4=fov end
							end
						end

						x1,x2=rnd(tan(a3)/fovT*wdthH),rnd(tan(a4)/fovT*wdthH)

						if x1~=x2 then
							d1,d2=dist(pp[1],p1),dist(pp[1],p2)

							aNorm=seg[3]+90
							aOff=aNorm-ga1
							txOff1=d1*m.sin(aOff/180*pi)
							d3=(d1*cos(aOff))
							if a1~=a3 then 
								d1=d3/cos(aNorm-(a3+pp[3]))
							end
							if a2~=a4 then 
								d2=d3/cos(aNorm-(a4+pp[3]))
							end

							d1,d2=d1*cos(a3),d2*cos(a4)

							k=seg[5]+6
							front=(x1>x2)
							if front and line[k]~=0 then

								double=line[3]&4>0
								if double then
									sec1,sec2=M[8][M[3][line[6]][6]],M[8][M[3][line[7]][6]]
								end

								side=M[3][line[k]]
								parts={side[3],side[4],side[5]}

								sec,tpRnd,btRnd=M[8][side[6]]

								for n,v in ipairs(parts) do
									render=v>0
									calculate=trueVar

									if (render or (n==3 and not (tpRnd and btRnd)))and (n==3 or double)then
										sky=falseVar
										yOff=0
										if n<3 then
											sky=n==1 and mx(sec1[4],sec2[4])==0
											y1,y2=sec1[3-n],sec2[3-n]
											calculate=(y1<y2)~=(n==2)~=(k==6)and y1~=y2 and sec1~=sec2
											y1,y2=mn(y1,y2),mx(y1,y2)
											if calculate then 
												if n==1then
													tpRnd=trueVar
												else
													btRnd=trueVar
													yOff=line[3]&16>0 and mx(sec1[2],sec2[2])-y2 or 0
												end
											end
										else
											if double then
												y1,y2=mx(sec1[1],sec2[1]),mn(sec1[2],sec2[2])
												calculate=sec1~=sec2
											else
												y1,y2=sec[1],sec[2]
											end
										end
										y1,y2=y1-pp[2],y2-pp[2]
										ys1,ys2=y1*vMult,y2*vMult

										if (calculate or render) and not sky then

											txOff2=seg[6]-side[1]
											if line[4]==48 then
												txOff2=txOff2-tick
											end

											yb1,yt1=ys1/d1,ys2/d1
											yb2,yt2=ys1/d2,ys2/d2

											xLast=0
											passL=falseVar

											if render then
												cr=M[21][v][4]
												if (seg[4]==switchedSwitch or difficulty==line[4]) and cr>0then
													v=cr
												end
												resScl=M[21][v][3]
												
												flip=1
												if (n==3 and line[3]&16>0) or (n==1 and line[3]&8==0) then
													flip=-1
												end
											end

											for k=x1,x2,-1 do
												ang=(aNorm-pp[3])-xAng[k]
												x = wdthH-k
												pass=falseVar
												if x>=0 and x<=wdth-1 then
													if i<dpth[x] then
														lrp=(k-x1)/(x2-x1)
														yb,yt=(yb1*(1-lrp)+yb2*lrp),(yt1*(1-lrp)+yt2*lrp)
														if absFunc(yt+yb)-(yt-yb)<hght then
															if render then
																if yb~=yt then
																	pass=trueVar
																	cD=d3*tan(ang)
																	cScl=mn(((absFunc(cD)+absFunc(d3))//LOD)+1,4)
																	cSclH=mn(rnd2(flr(cScl/cos(ang))),16)
																	cScl=rnd2(cScl)

																	xCur=flr((mx(cD-txOff1,0)-txOff2)/(resScl*cSclH))*cSclH
																	dCur={x,hghtH-yb,hghtH-yt,v,xCur,y2-y1,sec[5],side[2]+yOff,trueVar,resScl*cScl,cScl,flip,not passL,n==3 and double}
																	if xCur>xLast or (not passL) or k==x2 then

																		xLast=xCur-1+cSclH
																		passL=trueVar
																		walls[i][#walls[i]+1]=dCur
																	end
																	dLast=dCur
																end
															end
															
															if calculate then
																if n~=2 then
																	if yt<clH[x]then
																		vises[i][#vises[i]+1]={x,mx(yt,flH[x]),clH[x],sec,2}
																	end
																	if n==3then yNew=yt else yNew=yb end
																	if clH[x]>yNew then clH[x]=yNew end
																end
																if n~=1 then
																	if yb>flH[x]then
																		vises[i][#vises[i]+1]={x,flH[x],mn(yb,clH[x]),sec,1}
																	end
																	if n==3then yNew=yb else yNew=yt end
																	if flH[x]<yNew then flH[x]=yNew end
																end
																if (clH[x]<=flH[x])or (n==3 and (not double)and render) then
																	dpth[x]=i
																	lnLft=lnLft-1
																end
															end
														end
													end
												end
												if (not pass) and passL then
													passL=falseVar
													walls[i][#walls[i]+1]=dLast
													walls[i][#walls[i]][9]=falseVar
												end
											end
											if #walls[i]>0 then
												walls[i][#walls[i]][9]=falseVar
											end
										end
									end
								end
							end
						end
					end
				end

				i=i+1
			end
			
			
		end


	end


end

function onDraw()
	screenVar=screen
	local tri,rec,stCl,text=screenVar.drawTriangleF,screenVar.drawRectF,screenVar.setColor,screenVar.drawText
	mN=mN+1

	if mN<=1 then

		if loaded then

			tex=M[24][1]
			tW,tH=tex[1],tex[2]
			scl=wdth/tW
			for i=0,tW do
				x1=(tW/2-i-1+pp[3]/90*tW)%tW
				x2=(x1%1-1)*scl
				x1=flr(x1)*tH
				for j=0,tH-1 do
					pix=tex[5+j+x1]
					col=M[20][pix]
					stCl(col[1],col[2],col[3])
					rec(i*scl+x2,j*scl,scl,scl)
				end
			end

			for i=#walls,1,-1 do
				for j=1,#walls[i] do
				v=walls[i][j]
				if v[9] or v[13] then
					if v[9] then
						v2=walls[i][j+1]
					else
						v2=v
					end
					tex=M[21][v[4]]
					flip=v[12]
					y=mn(flip,0)
					x=v[1]
					x2=v2[1]

					fin=v[2-y]
					fin2=v2[2-y]

					k=v[3+y]
					k2=v2[3+y]

					if not v2[9] then x2=x2+1 end

					lght=mn(v[7]+screenBrightOffset,1)^2.2

					yScl=flip*(v[2]-v[3])*v[10]/v[6]
					yScl2=flip*(v2[2]-v2[3])*v[10]/v2[6]

					crM=flip>0 and mn or mx
					itter=0
					while k*flip<fin*flip and (itter<tex[2] or not v[14]) do

						kN=crM(k+yScl,fin)
						k2N=crM(k2+yScl2,fin2)

						pix=tex[6+((y*v[11]+v[8]//tex[3])%tex[2])+tex[2]*(v[5]%tex[1])]
						col=M[20][pix]
						if col then
							stCl(col[1]*lght,col[2]*lght,col[3]*lght)
							tri(x,k,x,kN,x2,k2N)
							tri(x,k,x2,k2,x2,k2N)
						end

						k=kN
						k2=k2N
						y=y+flip
						itter=itter+v[11]

						end

					end
				end

				for j,v in ipairs(vises[i]) do
					sec=v[4]
					if sec[v[5]+2]~=0 then
						tex=M[22][sec[v[5]+2]]
						x=v[1]
						lght=mn(sec[5]+screenBrightOffset,1)^2.2
						col=M[20][tex[4]]
						stCl(col[1]*lght,col[2]*lght,col[3]*lght)
						screen.drawLine(x,-v[3]+hghtH-1,x,-v[2]+hghtH)
					end
				end

				for j=1,#thngsOrd[i] do
					cr=M[1][thngsOrd[i][j]]
					if cr[6]~=0 then
						pl1=sub(cr,pp[1])
						d1=cr[20]
						if d1>1 then
							a1=wrap(at2(pl1)-pp[3])
							d1=d1*cos(a1)
							if absFunc(a1)<90 then
								x1=wdthH-rnd(tan(a1)/fovT*wdthH)
								ang=rnd((180+a1+pp[3]-cr[3])/360*8)
								state=M[16][cr[6]][1]
								if state~=0 and cr[6]~=1 then
									tex=M[17][absFunc(state)][ang%8+1] --(cr[15]//10)%#tex+1
									flip=tex<0 and -1 or 1
									tex=absFunc(tex)
									tex=M[23][tex]
									tW,tH=tex[1],tex[2]
									cScl=d1<LOD and 1 or 2
									scl=wdthH/(fovT*d1)
									sclV=scl*pixelAspectCorrection
									yb=hghtH+(pp[2]-cr[9])/d1*vMult
									yt=yb-tex[5]*sclV
									x2=x1-flip*tex[4]*scl
									scl,sclV=scl*tex[3],sclV*tex[3]
									lght=state>0 and mn(M[8][cr[8]][5]+screenBrightOffset,1)^2.2 or 1
									pxSize=scl*cScl
									pxSizeV=pxSize*pixelAspectCorrection
									if cr[4] and M[15][cr[4]][23]&8>0 then
										for k=0,tW-1,cScl do
											x1=x2+k*scl*flip
											if i<=dpth[clmp(rnd(x1),0,wdth-1)] then
												for n=0,tH-1,cScl do
													pix=tex[7+n+k*tH]
													if pix~= 0 then
														fuzz=fuzz%50+1
														stCl(0,0,0,mn(75*M[13][2][fuzz],255))
														rec(x1,yt+n*sclV,pxSize,pxSizeV)
													end
												end
											end
										end
									else
										for k=0,tW-1,cScl do
											x1=x2+k*scl*flip
											if i<=dpth[clmp(rnd(x1),0,wdth-1)] then
												for n=0,tH-1,cScl do
													pix=tex[7+n+k*tH]
													if pix~= 0 then
														col=M[20][pix]
														stCl(col[1]*lght,col[2]*lght,col[3]*lght)
														rec(x1,yt+n*sclV,pxSize,pxSizeV)
													end
												end
											end
										end
									end
								end
							end
						end
					end
				end
			end
		end
	end
end