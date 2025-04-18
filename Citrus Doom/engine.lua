m=math
mx=m.max
mn=m.min
flr=m.floor
pi=m.pi
gN=input.getNumber
gB=input.getBool
sB=output.setBool
trueVar=true
falseVar=false
ipairsVar=ipairs
abs=m.abs
tableRemove=table.remove

function add(a,b)return{(a[1]+b[1]),(a[2]+b[2])}end
function sub(a,b)return{(a[1]-b[1]),(a[2]-b[2])}end
function s(a)return m.sin(a/180*pi)end
function c(a)return m.cos(a/180*pi)end
function at2(a,b)return m.atan(b[2]-a[2],b[1]-a[1])*180/pi end
function clmp(a,b,c)return mx(mn(c,a),b)end
function dist(a,b)return m.sqrt(((a[1]-b[1])^2)+((a[2]-b[2])^2))end
function dVec(a,b)return{c(a)*b,s(a)*b}end
function exp(a)return a[1],a[2]end

M={}
romCr=1
levelCr=3
loaded=falseVar
init=trueVar
weapon=2
pIn=0
weaponFireDelay=0
httpTk=0
timePassage=0
pRandom=0
stg=1
lookAcl=0
difficulty=2

function findMe(i,a,cr)
	if i<32768then
		cr=M[7][i]
		return findMe(cr[cr[3]*(a[2]-cr[2])-cr[4]*(a[1]-cr[1])>0 and 8 or 7],a)
	else
		i=M[5][M[6][i-32768][2]]
		return M[8][M[3][M[2][i[4]][i[5]+6]][6]]
	end
end

function chkPs(p,mv,index,cr,i,j)
	s1=M[15][M[1][index][4]]
	r,h=s1[18],s1[19]
	bstDst=r
	blkPs=sub(p,M[10][1])
	blkCr=M[10][2+blkPs[1]//128+blkPs[2]//128*blockmapLim]
	for i,cr in ipairsVar(blkCr[0]) do
		pos=M[1][cr]
		if cr~=index and pos and M[1][index][14]~=cr then
			dst=dist(pos,p)
			s2=M[15][pos[4]]
			if pos[20] then
				x1=dst-s2[18]
				if x1<bstDst and s2[23]&1>0 and (s1[23]&1>0 or (p[9]+h<pos[9] or p[9]>pos[9]+s2[19])==falseVar)then
					hitThing=pos
					if mv==falseVar then
						return falseVar
					end
					bstDst=x1
					bstA=at2(p,pos)
				end
			end
			if index==pIn and not pos[10]then-- the not pos 10 is to prevent the player picking something up which hasn't been spawned in the renderer
				if dst<50then
					a=s2[25]
					if a>0then
						for n,v in ipairsVar(M[12][a])do
							if v>0 and M[12][1][n]<M[12][2][n]then
								pos=M[12]
								M[1][cr]=falseVar
								pos[1][n]=flr(mn(pos[1][n]+v,pos[2][n]))
								if clmp(n,5,11)==n then
									weapon=n-4
								end
							end
						end
					end
					a=s2[29]
					if a>0 then
						a=M[11][a]
						for n=7,8 do
							pTng[n]=clmp(pTng[n]+a[n*2-13],pTng[n],a[n*2-12])
						end
						M[1][cr]=falseVar
					end
				end
			end
		end
	end
			
	hitThing=falseVar
	bounds=findMe(#M[7],p)
	bt,tp=exp(bounds)

	if tp-bt<h or bt>p[9]+24then-- or tp<p[9]+h
		return falseVar
	end
	for i=1,#blkCr do
		cr=M[2][blkCr[i]]
		dst,tmpA=chkLnDst(p,M[4][cr[1]],M[4][cr[2]])
		if dst<bstDst then
			if index==pIn and cr[4]==2 then -- only activate special if it's the player and the special is a walk over
				thinkers[M[8][M[9][cr[5]][1]][9]or#thinkers+1]={cr[5],1}-- if thinker exists, replace it, if not, create new one
			end
			if (cr[3]&1>0 and s1[23]&1>0) or cr[3]&4==0 then
				bstDst=dst
				bstA=tmpA
			else
				tmpTp,tmpBt=mn(cr[9],tp),mx(cr[8],bt)
				if mn(p[9],tp-h)+24<tmpBt or mx(p[9],bt)+h>tmpTp then
					bstDst=dst
					bstA=tmpA
				else
					tp,bt=tmpTp,tmpBt
				end
			end
		end
	end
	bounds={bt,tp}
	if mv then
		if bstDst~=r then
			cr=add(p,dVec(bstA,bstDst-r))
			p[1]=cr[1]
			p[2]=cr[2]
		end
		return trueVar
	end
	return bstDst==r
end

function chkLnDst(p1,p2,p3)
	d1=dist(p2,p1)
	aNorm=at2(p2,p3)+90
	aOff=aNorm-at2(p1,p2)
	hOff=-d1*s(aOff)
	d3=d1*c(aOff)
	aPsh=aNorm
	if d3<0 then
		aPsh=aPsh+180
	end
	if hOff<0 then
		return d1,at2(p1,p2)
	elseif hOff>dist(p3,p2) then
		return dist(p3,p1),at2(p1,p3)
	else
		return abs(d3),aPsh
	end
end

function chkRayCol(p1,p2,level,index,cr)
	bsDst=dist(p1,p2)
	crDst=bsDst
	pass=trueVar
	x1,y1=exp(p1)
	x2,y2=exp(p2)
	x21,y21=exp(sub(p2,p1))
	h1,h2=p1[9]+32,p2[9]+32
	valid=falseVar
	for i,cr in ipairsVar(M[2])do
		x3y3=M[4][cr[1]]
		x43,y43=exp(sub(M[4][cr[2]],x3y3))
		x13,y13=exp(sub(p1,x3y3))
		crMl=y43*x21-x43*y21
		uA=(x43*y13-y43*x13)/crMl
		uB=(x21*y13-y21*x13)/crMl
		if clmp(uA,0,1)==uA and clmp(uB,0,1)==uB then
			crPos={x1+(uA*x21),y1+(uA*y21)}
			dst=dist(p1,crPos)
			intH=h1+(h2-h1)*(dst/bsDst)
			if clmp(intH,cr[8],cr[9])~=intH then
				pass=falseVar
				if level==1 then
					return falseVar
				end
				if dst<crDst then
					crDst=dst
					crX,crY=exp(crPos)
					crH=intH
					crI=i
				end
			end
		end
	end
	
	if level>1 then
		if level==3 then
			for i,cr in ipairsVar(M[1]) do
				if cr and i~=index then
					s1=M[15][cr[4]]
					if s1[23]&1>0 and cr[20] then
						dst=dist(p1,cr)
						if dst<crDst then
							uA=chkLnDst(cr,p1,p2)
							d1=(dst/bsDst)
							intH=h1+(h2-h1)*d1
							if clmp(intH,cr[9],cr[9]+s1[19])==intH and uA<s1[18] then
								valid=trueVar
								pass=falseVar
								crX=x1+(x2-x1)*d1
								crY=y1+(y2-y1)*d1
								crH=intH
								crI=i
							end
						end
					end
				end
			end
		end
		return pass,crI,{crX,crY,crH}
	end
	return trueVar
end

function httpReply(a,b,c)
	httpTkP=httpTk//2
	httpTk=0
end

function rand()
	pRandom=pRandom%256+1
	return M[13][1][pRandom]
end

function damageThing(cr,i)-- thing array, damage, function declaration variables are local so the most common should be used
	s1=M[15][cr[4]]
	if s1[23]&2>0 and cr[7]>0 then
		cr[8]=cr[8]-(i+1)//2
		cr[7]=cr[7]-i//2+mn(cr[8],0)
		cr[8]=mx(cr[8],0)
		if rand()<s1[10] then
			cr[6]=s1[9]
			cr[15]=0
			cr[23]=pTng
			cr[10]=trueVar
		end
	end
end

function chkView(a,b,angle)
	return b[20]and abs(((at2(a,b)-a[3]+180)%360)-180)<angle and chkRayCol(a,b,1)
end

function fireWeapon(source,index)
	ramp=targ and (targ[9]-source[9])*crWeapon[6]/dist(targ,source)or 0
	for i=1,crWeapon[12]do
		a={}
		for i=1,19 do
			a[i]=0
		end
		a[4]=crWeapon[8]
		a[7]=1000
		a[10]=trueVar
		a[14]=index
		
		spreadOff=(rand()/128-1)*crWeapon[10]
		vel=dVec(source[3]+spreadOff,crWeapon[6])
		if crWeapon[7]>0then
			M[1][#M[1]+1]=a
			for j=1,3 do
				a[j]=source[j]
			end
			s1=M[15][a[4]]
			a[6]=s1[3]
			a[9]=source[9]+32
			a[11]=vel[1]
			a[12]=vel[2]
			a[17]=weapon
			a[19]=ramp
		else
			pos=add(source,vel)
			pos[9]=pTng[9]+ramp
			thingExists,wall,pos=chkRayCol(source,pos,3,index)
			if not thingExists then
				posOff=sub(pos,dVec(source[3]+spreadOff,1))
				M[1][#M[1]+1]=a
				a[1]=posOff[1]
				a[2]=posOff[2]
				a[6]=M[15][a[4]][3]
				a[9]=pos[3]
				a[19]=1
				if valid then
					a=M[1][wall]
					damageThing(a,crWeapon[9]*((rand()&3)+2))
				end
			end
		end
	end
end

function onTick()
	sB(9,gB(32))
	sB(2,falseVar)
	sB(3,falseVar)

	for j=1,3 do
		if gB(32)and (not loaded)or not M[21]then
			rom=property.getText(romCr.."")
			if rom~="" then
				i=1
				nm=""
				cr=string.sub(rom,i,i)
				while nm.. cr~=""do
					if cr==","or cr==""then
						nm=nm+0
						if stg==1then
							crI=nm
							if M[nm]==nilVar then
								M[nm]={}
							end
							stg=2
						elseif stg==2then
							intH=nm
							crL=0
							stg=3
						elseif stg==3then
							cnt=nm
							stg=4
						else
							if crL==0then
								crL=intH
								cnt=cnt-1
								crM={}
								M[crI][#M[crI]+1]=crM
							end
							crM[#crM+1]=nm
							crL=crL-1
							if mx(crL,cnt)==0then
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
		if init then
			thinkers,init={}
			sndLst=1
			for i=1,10 do
				M[i]=M[i+10*levelCr]
			end
			for i=14,16 do
				M[12][1][i]=0
			end
			levelCr=levelCr+1
			for i,cr in ipairsVar(M[1])do
				for j=7,20 do
					cr[j]=0
				end
				cr[7]=M[15][cr[4]][4]-- health
				cr[9],cr[10]=findMe(#M[7],cr)[1]-- vertical position
				--cr[10]=falseVar-- send update to render block, set to nil above which counts as false
				--cr[20]=trueVar-- alive state, set to zero above which counts as true
				if cr[4]==1 then-- identify player
					if pTng then
						cr[7]=pTng[7]
						cr[8]=pTng[8]
					end
					pIn=i
					pTng=cr
				elseif cr[5]&difficulty<1then
					M[1][i]=falseVar
				end
			end
			blockmapLim=M[10][1][3]
		end

		for i,cr in ipairsVar(M[2])do -- refresh walls
			if cr[3]&4>0 then
				s1,s2=M[8][M[3][cr[6]][6]],M[8][M[3][cr[7]][6]]
				cr[8]=mx(s1[1],s2[1])
				cr[9],s1[9],s2[9]=mn(s1[2],s2[2])
			else
				cr[8],cr[9]=0,0
			end
		end
		
		out={}
		for i=1,32 do
			out[i]=0
		end
		
		timePassage=mn(timePassage+1/httpTkP,2/35)
		sB(1,timePassage>=0)
		if timePassage>=0 then
			timePassage=timePassage-1/35
			
			for i=2,#M[10]do
				M[10][i][0]={}
			end
			
			for i,cr in ipairsVar(M[9])do
				cr[6]=falseVar
			end
			
			for i,v in ipairsVar(thinkers)do			
				cr=M[9][v[1]]
				pos=M[8][cr[1]]
				s1=pos[cr[2]]
				if s1==cr[3] then
					thinkers[i]=v[2]==cr[4]and{cr[5],0}or{v[1],v[2]+1}
					if cr[5]==0 then
						tableRemove(thinkers,i)
					end
				else
					pos[8]=pos[8]or s1~=v
					pos[cr[2]]=clmp(cr[3],s1-2,s1+2)
				end
				pos[9]=i
			end
			
			for i,cr in ipairsVar(M[1])do
				if cr then
					for j,v in ipairsVar({1,2,9})do-- updates position based on velocity
						cr[v]=cr[v]+cr[v+10]
					end
					cr[15]=cr[15]+1
					s1=M[15][cr[4]]
					if cr[7]<=0 and cr[20]then
						cr[15]=0
						cr[6]=s1[cr[7]<=-s1[4] and s1[15]>1 and 15or 14]-- to gib or not to gib
						cr[10],cr[20]=trueVar
						if s1[27]>0 then-- item drop logic, copies what died and turns it into a pickup
							pos={}
							for j=1,30 do-- just to make sure it copies the entire thing
								pos[j]=cr[j]
							end
							pos[4]=s1[27]
							pos[6]=s1[28]
							M[1][#M[1]+1]=pos
						end
					end
					state=M[16][cr[6]]
					
					if cr[15]>=state[2] and state[2]~=-1then
						cr[6]=state[4]
						cr[15]=0
						state3=M[16][cr[6]][3]
						if state3==1 then-- explode logic
							for i,stg in ipairsVar(M[1]) do
								if stg then
									nm=128-dist(cr,stg)
									if nm>0 then
										damageThing(stg,nm)
									end
								end
							end
						elseif state3==2then-- view logic
							if chkView(cr,pTng,90) then
								cr[23]=pTng-- set target
								cr[6]=s1[5]
							end
						elseif state3==3then-- chase logic
							angle=flr(at2(cr,cr[23])/45+0.5)*45
							valid=falseVar
							stg=1
							while stg<5 and not valid do-- checks angles 0, 45, -45, 90, -90 relative to desired direction
								nm=add(cr,dVec(angle+M[19][2][stg],8))
								nm[9]=cr[9]
								stg=stg+1
								valid=chkPs(nm,falseVar,i)and bounds[1]>=nm[9]-24
							end
							if valid then
								cr[1]=nm[1]
								cr[2]=nm[2]
								cr[3]=angle
								cr[9]=bounds[1]
								cr[10]=trueVar
							end
							a=dist(cr,cr[23])
							if s1[13]>0 and chkRayCol(cr,cr[23],1)and mn(a,230)<rand()then
								cr[6]=s1[13]
							end
							if a<64 and s1[12]>0then
								cr[6]=s1[12]
							end
						elseif state3>9then-- attack logic
							cr[3]=at2(cr,cr[23])
							crWeapon=M[14][state3]
							cr[10]=trueVar
							targ=cr[23]
							fireWeapon(cr,i)
						end
					end
					if cr[17] and cr[17]>0then
						crWeapon=M[14][cr[17]]
						if not chkPs(cr,falseVar,i) or cr[9]<=bounds[1] then
							if hitThing then
								damageThing(hitThing,s1[21]*((rand()&7)+1))
							end
							cr[1]=cr[1]-cr[11]
							cr[2]=cr[2]-cr[12]
							cr[3]=0
							cr[6]=M[15][cr[4]][14]
							cr[10]=trueVar
							cr[11]=0
							cr[12]=0
							cr[17]=nilVar
							cr[19]=0
						end
					end
					if cr[6]==1then
						M[1][i]=falseVar
					else
						blkPs=sub(cr,M[10][1])
						blkCr=M[10][2+blkPs[1]//128+blkPs[2]//128*blockmapLim]
						if blkCr~=nilVar then
							blkCr[0][#blkCr[0]+1]=i
						end
					end
				end
			end
			
			for i=1,8 do
				if gB(i)and M[12][1][i+4]>0then
					weapon=i
				end
			end
			
			crWeapon=M[14][weapon]
			
			
			pTng[3]=pTng[3]-gN(3)*(clmp(lookAcl,5,6)*1.5-6)-- lookAcl>5 and 3 or 1.5
			lookAcl=abs(gN(3))*lookAcl+1
			pp=pTng
			for i=1,2 do
				pp=add(pp,dVec(pTng[3]-180+90*i,gN(i)*8.33))
			end
			pp[9]=pTng[9]
			for i=1,8 do
				valid=chkPs(pp,trueVar,pIn)
			end
			if valid then
				for i=1,2 do
					pTng[i]=pp[i]
				end
				if pTng[9]<=bounds[1]then
					pTng[9]=mn(bounds[1],pTng[9]+4)
					pTng[19]=mx(0,pTng[19])
				else
					if pTng[9]>=bounds[2]-56then
						pTng[9]=bounds[2]-56
						pTng[19]=mn(0,pTng[19])
					end
					pTng[19]=pTng[19]-1
				end
			end
			
			ammo=M[12][1]
			pos=crWeapon[1]
			if gB(31) and weaponFireDelay<=0 and (pos==0 or ammo[pos]>=crWeapon[2])then -- player shooting logic
				sB(3,trueVar) -- announces player is firing
				weaponFireDelay=crWeapon[3]
				if pos>0then -- drain ammo
					ammo[pos]=ammo[pos]-crWeapon[2]
				end
				rampBst,targ=2048
				for i,cr in ipairsVar(M[1])do -- vertical auto aim
					if i~=pIn and cr and chkView(pTng,cr,10)then
						dst=dist(cr,pTng)
						if dst<rampBst then
							if M[15][cr[4]][23]&2>0then
								targ=cr
								rampBst=dst
							end
						end
					end
				end
				
				fireWeapon(pTng,pIn)
			end
			weaponFireDelay=weaponFireDelay-1
			
			if gN(4)<0 then -- interacting with doors/linedefs in general
				cr=add(pTng,dVec(pTng[3],64))
				cr[9]=pTng[9]
				thingExists,wall=chkRayCol(pTng,cr,2,pIn)
				cr=M[2][wall]
				if thingExists==falseVar then
					out[2]=wall
					pos,valid=cr[4]
					for i=14,16 do-- used for keyed doors
						valid=valid or M[12][1][i]>0 and pos==i
					end
					if pos==1 or valid then
						thinkers[M[8][M[9][cr[5]][1]][9]or #thinkers+1]={cr[5],1}-- if thinker exists, replace it, if not, create new one
					elseif pos==11then
						init=trueVar
						sB(2,trueVar)
					elseif pos>3000 and pos<3005then
						difficulty=flr(pos-3000)
					end
				end
			end

			--for i,cr in ipairsVar(M[8])do -- moves doors, old implementation
			--	if cr[10]then
			--		if cr[10]>2then
			--			cr[2]=cr[2]-2
			--			if cr[2]==cr[1]then
			--				cr[10]=nilVar
			--			end
			--			refWlls=trueVar
			--			cr[8]=trueVar
			--		elseif cr[10]>1then
			--			cr[11]=cr[11]+1
			--			if cr[11]>159then
			--				cr[10]=3
			--			end
			--		else
			--			cr[2]=cr[2]+2
			--			if cr[2]==cr[9]-4then
			--				cr[10]=2
			--				cr[11]=0
			--			end
			--			refWlls=trueVar
			--			cr[8]=trueVar
			--		end
			--	end
			--end
		end

		

		out[1]=weapon
		for i=3,8 do
			out[i]=pTng[M[19][4][i]]-- M[19][4] is 0,7,8,0,1,2,9,3
		end
		out[5]=pIn
		out[13]=pTng[3]

		i=sndLst
		running=trueVar
		slt=1
		ttEnd=#M[1]+#M[8]
		while slt<3 and running do
			pos=slt*9+5
			if i<=#M[1] then
				cr=M[1][i]
				if i~=pIn then
					if cr then
						if cr[10] then
							cr[10]=falseVar
							out[pos]=i
							for j=1,8 do
								out[pos+j]=cr[M[19][1][j]]-- M[19][1] is 1,2,9,6,11,12,19,3
							end
							slt=slt+1
						end
					else
						out[pos]=-i
						tableRemove(M[1],i)
						slt=slt+1
						ttEnd=ttEnd-1
					end
				end
			else
				cr=M[8][i-#M[1]]
				if cr[8] then
					cr[8]=falseVar
					out[pos]=i-#M[1]+2^15
					out[pos+1]=cr[1]
					out[pos+2]=cr[2]
					slt=slt+1
				end
			end
			i=((i-2)%ttEnd)+1
			sndLst=mn(sndLst,ttEnd)
			running=i~=sndLst
		end
		sndLst=i

		for i=1,32 do
			output.setNumber(i,out[i])
		end
	end

	httpTk=httpTk+1
	async.httpGet(8,"")
end

function onDraw()
	text=screen.drawText
	
	text(26,137,httpTkP)
	
	if loaded then
		for i=1,4 do
			a=124+i*7
			text(240,a,flr(M[12][1][i]))
			text(230,a,M[12][1][13+i])
		end
		text(26,143,mn(difficulty,3))
	end
end