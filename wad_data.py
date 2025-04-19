from clipboard import copy as SetC
from wad_reader import WADReader
from asset_data import AssetData
from math import dist, floor as flr
from code_compressor import compress
import pygame, time, json
from copy import deepcopy as dcopy
import os

def off_add(a,b):
    return (a[0],a[1]+b)

class WADData:
    LUMP_INDICES = {
        'THINGS': 1, 'LINEDEFS': 2, 'SIDEDEFS': 3, 'VERTEXES': 4, 'SEGS': 5,
        'SSECTORS': 6, 'NODES': 7, 'SECTORS': 8, 'REJECT': 9, 'BLOCKMAP': 10
    }
    LINEDEF_FLAGS = {
        'BLOCKING': 1, 'BLOCK_MONSTERS': 2, 'TWO_SIDED': 4, 'DONT_PEG_TOP': 8,
        'DONT_PEG_BOTTOM': 16, 'SECRET': 32, 'SOUND_BLOCK': 64, 'DONT_DRAW': 128, 'MAPPED': 256
    }

    def __init__(self, WAD, map_name, import_textures=True):
        self.reader = WADReader(WAD)

        self.map_index = self.get_lump_index(lump_name=map_name)
        assert str(self.map_index) != str(False), "Map not in WAD"
            
        self.vertexes = self.get_lump_data(
            reader_func=self.reader.read_vertex,
            lump_index=self.map_index + self.LUMP_INDICES['VERTEXES'],
            num_bytes=4  # num bytes per vertex
        )
        self.linedefs = self.get_lump_data(
            reader_func=self.reader.read_linedef,
            lump_index=self.map_index + self.LUMP_INDICES['LINEDEFS'],
            num_bytes=14
        )
        self.nodes = self.get_lump_data(
            reader_func=self.reader.read_node,
            lump_index=self.map_index + self.LUMP_INDICES['NODES'],
            num_bytes=28
        )
        self.sub_sectors = self.get_lump_data(
            reader_func=self.reader.read_sub_sector,
            lump_index=self.map_index + self.LUMP_INDICES['SSECTORS'],
            num_bytes=4
        )
        self.segments = self.get_lump_data(
            reader_func=self.reader.read_segment,
            lump_index=self.map_index + self.LUMP_INDICES['SEGS'],
            num_bytes=12
        )
        self.things = self.get_lump_data(
            reader_func=self.reader.read_thing,
            lump_index=self.map_index + self.LUMP_INDICES['THINGS'],
            num_bytes=10
        )
        self.sidedefs = self.get_lump_data(
            reader_func=self.reader.read_sidedef,
            lump_index=self.map_index + self.LUMP_INDICES['SIDEDEFS'],
            num_bytes=30
        )
        self.sectors = self.get_lump_data(
            reader_func=self.reader.read_sector,
            lump_index=self.map_index + self.LUMP_INDICES['SECTORS'],
            num_bytes=26
        )
        self.blockmap = self.get_lump_data(
            reader_func=self.reader.read_blockmap,
            lump_index=self.map_index + self.LUMP_INDICES['BLOCKMAP'],
            num_bytes=2
        )
        #self.sound = self.get_lump_data(
        #    reader_func=self.reader.read_blockmap,
        #    lump_index=self.map_index + self.LUMP_INDICES['DPSGCOCK'],
        #    num_bytes=2
        #)

        

        self.update_data()
        # ------------------------------- #
        if import_textures:
            self.asset_data = AssetData(self)
            self.sounds = {}
            for i in ["DPBFG"]:
                self.sounds[i] = self.asset_data.load_sound(i)
        # ------------------------------- #
        self.reader.close()

    def update_data(self):
        self.update_linedefs()
        self.update_sidedefs()
        self.update_segs()

    def update_sidedefs(self):
        for sidedef in self.sidedefs:
            sidedef.sector = self.sectors[sidedef.sector_id]

    def update_linedefs(self):
        for linedef in self.linedefs:
            linedef.front_sidedef = self.sidedefs[linedef.front_sidedef_id]
            #
            if linedef.back_sidedef_id == 0xFFFF:  # undefined sidedef
                linedef.back_sidedef = None
            else:
                linedef.back_sidedef = self.sidedefs[linedef.back_sidedef_id]

    def update_segs(self):
        for seg in self.segments:
            seg.start_vertex = self.vertexes[seg.start_vertex_id]
            seg.end_vertex = self.vertexes[seg.end_vertex_id]
            seg.linedef = self.linedefs[seg.linedef_id]
            #
            if seg.direction:
                front_sidedef = seg.linedef.back_sidedef
                back_sidedef = seg.linedef.front_sidedef
            else:
                front_sidedef = seg.linedef.front_sidedef
                back_sidedef = seg.linedef.back_sidedef
            #
            seg.front_sector = front_sidedef.sector
            if self.LINEDEF_FLAGS['TWO_SIDED'] & seg.linedef.flags:
                seg.back_sector = back_sidedef.sector
            else:
                seg.back_sector = None

            # convert angles from BAMS to degrees
            seg.angle = (seg.angle << 16) * 8.38190317e-8
            seg.angle = seg.angle + 360 if seg.angle < 0 else seg.angle

            # texture special case
            if seg.front_sector and seg.back_sector and False: #do not want
                if front_sidedef.upper_texture == '-':
                    seg.linedef.front_sidedef.upper_texture = back_sidedef.upper_texture
                if front_sidedef.lower_texture == '-':
                    seg.linedef.front_sidedef.lower_texture = back_sidedef.lower_texture

    @staticmethod
    def print_attrs(obj):
        print()
        for attr in obj.__slots__:
            print(eval(f'obj.{attr}'), end=' ')

    def get_lump_data(self, reader_func, lump_index, num_bytes, header_length=0):
        lump_info = self.reader.directory[lump_index]
        if num_bytes != -1:
            count = lump_info['lump_size'] // num_bytes
            data = []
            for i in range(count):
                offset = off_add(lump_info['lump_offset'],i * num_bytes + header_length)
                data.append(reader_func(offset))
            return data
            

    def get_lump_index(self, lump_name, start=0):
        for index, lump_info in enumerate(self.reader.directory):
            #print(lump_info.values())
            if lump_name in lump_info.values() and index >= start:
                #print("OK")
                return index
        return False

def sq(a):
    factor=2.2
    return tuple([round((i**factor)/(255**(factor-1))) for i in a])

def add(a,b):
    return tuple([a[i]+b[i] for i in range(len(a))])

def div(a,b):
    return tuple([i/b for i in a])

def insert_thinker(thinker):
    global sector_thinkers
    
    if thinker in sector_thinkers:
        return sector_thinkers.index(thinker)+1
    else:
        sector_thinkers.append(thinker)
        return len(sector_thinkers)

def find_sector(tag):
    global level_wad

    for index in range(len(level_wad.sectors)):
        i = level_wad.sectors[index]
        if i.tag == tag:
            return index+1
    return 0

if __name__ == '__main__':
    start_time=time.time()
    #,"weapons_at_start.wad","jump_to_crash_zone.wad"
    file_name=["DOOM.WAD","settings_map.wad"] # more rightwards ones overwrite leftwards ones
    #map_order=["E"+str(1+i//9)+"M"+str(1+i%9) for i in range(3*9)]
    #map_order=["E1M2"]
    #map_order=["SET1"]+map_order
    map_order=["SET1","E1M1","E1M2","E1M3","E1M4","E1M5","E1M6","E1M7","E1M8"]
    #map_order=["SET1","E1M1","E2M3"] # self explanitory, first level is the settings one
    wad = WADData(["wad/"+i for i in file_name], map_name=map_order[0])
    [print("loaded "+i) for i in file_name]
    #wad.asset_data.textures
    #print(wad.vertexes[wad.linedefs[0].start_vertex_id])
    #print(wad.vertexes[wad.linedefs[0].end_vertex_id])
    #print(len(wad.vertexes))
    #print(len(wad.linedefs))
    #print(wad.vertexes[0])
    #print(wad.linedefs[0].start_vertex_id,wad.linedefs[0].end_vertex_id,wad.linedefs[0].flags,wad.linedefs[0].line_type,wad.linedefs[0].sector_tag,wad.linedefs[0].front_sidedef_id,wad.linedefs[0].back_sidedef_id)
    file = open("things.txt")
    text = file.read()
    file.close()
    thing_lookup = {}
    thing_sprites = []
    for i in text.split("\n"):
        i=i.split("\t")
        thing_lookup[int(i[0])]=i[5]
        if not i[5] in thing_sprites: thing_sprites.append(i[5])
    #print(thing_lookup)
    #print(thing_sprites)

    obj_name = "Citrus Doom"
    base_name = "base_doom"

    path_bits = [os.getenv('APPDATA')+"\\Stormworks\\data\\vehicles\\",".xml"]
    path_in = base_name+".xml"
    path_out = path_bits[0]+obj_name+path_bits[1]

    wall_overrides={"EXITSIGN":1,"TEKWALL1":2,"EXITDOOR":2,"ORANGE_1":1,"KEYBOARD":1,"HOTAS2":1,"DIFFICUL":2} # used to make some walls higher quality than others
    sprite_overrides={"SHEL":1} # used to make some sprites higher quality than others, mostly generated automatically
                                # manually adjusted the shotgun shell pickup since it looks weird at 1/2
    
    orange = pygame.image.load("Orange.png")
    

    #print(wad.sound)
    #halt
    force_new_cache = False

    packets = []
    curmax = 4000
    res_scale_walls = 4
    res_scale_flats = 4
    res_scale_sprites = 2
    res_scale_sprites_quality = 2
    res_scale_sprites_projectiles = 2
    res_scale_sprites_weapons = 2
    res_scale_sprites_face = 1
    res_scale_sky = 4

    TICKRATE = 35

    wall_textures = [*wad.asset_data.wall_textures]
    flat_textures = [*wad.asset_data.flat_textures]
    sprite_textures = [*wad.asset_data.sprites]
    face_textures = [*wad.asset_data.face]
    all_sprites = wad.asset_data.sprites | wad.asset_data.face
    all_sprite_textures = [*all_sprites]
    
    wall_avs = {}
    flat_avs = {}
    sprite_avs = {}
    sky_av = 0
    wall_looker = ["-"]+wall_textures
    flat_looker = ["-"]+flat_textures
    pixels = 0
    num = 0

    blockmap_skip_first = False

    trans_colour = (152, 0, 136)

    for i in face_textures:
        sprite_overrides[i] = res_scale_sprites_face
    
    
    ammo_item_list = ["Bullet","Shell","Rocket","Cells","Fist","Pistol","Chainsaw","Shotgun","Chaingun","Rocket Launcher","Plasma Rifle",
                 "BFG","SSGun","Blue Key","Red Key","Yellow Key"
                 ]
    #print(len(ammo_item_list))
    
    ammo_pickup_list = [{"Bullet":50,"Fist":1,"Pistol":1},{"Bullet":200,"Shell":50,"Rocket":50,"Cells":300},
                   {"Bullet":10},{"Bullet":50},{"Bullet":20,"Chaingun":1},
                   {"Shell":4},{"Shell":20},{"Shell":8,"Shotgun":1},{"Shell":8,"SSGun":1},
                   {"Rocket":1},{"Rocket":5},{"Rocket":2,"Rocket Launcher":1},
                   {"Cells":20},{"Cells":100},{"Cells":40,"Plasma Rifle":1},{"Cells":40,"BFG":1},
                   {"Blue Key":1},{"Red Key":1},{"Yellow Key":1},
                   {"Chainsaw":1},
                   ]

    ammo_pickup_dict = {"MT_CLIP":3,"MT_MISC17":4,"MT_CHAINGUN":5,
                   "MT_MISC22":6,"MT_MISC23":7,"MT_SHOTGUN":8,"MT_SUPERSHOTGUN":9,
                   "MT_MISC18":10,"MT_MISC19":11,"MT_MISC27":12,
                   "MT_MISC20":13,"MT_MISC21":14,"MT_MISC28":15,"MT_MISC25":16,
                   "MT_MISC4":17,"MT_MISC5":18,"MT_MISC6":19,
                   "MT_MISC9":17,"MT_MISC8":18,"MT_MISC7":19,
                   "MT_MISC26":20,
                   }

    health_pickup_list = [("MT_MISC2",(1,200,0,0,0)), # health bonus/potion
                          ("MT_MISC10",(10,100,0,0,0)), # stimpack
                          ("MT_MISC11",(25,100,0,0,0)), # medkit
                          ("MT_MISC12",(100,200,0,0,0)), # sumpercharge/soul sphere
                          ("MT_MISC3",(0,0,1,200,0)), # armor bonus/helmet
                          ("MT_MISC0",(0,0,100,100,0.3)), # armor
                          ("MT_MISC1",(0,0,200,200,0.5)), # megaarmor/combat armor
                          ("MT_MEGA",(200,200,200,200,0.5)), # megasphere
                          ]
    health_pickup_list_zip = [[health_pickup_list[j][i] for j in range(len(health_pickup_list))] for i in range(len(health_pickup_list[0]))]

    key_indexes = {}
    for i in ["red","blue","yellow"]:
        key_indexes[i] = ammo_item_list.index(i[0].upper()+i[1:]+" Key")+1
    
    for index in range(len(ammo_pickup_list)):
        i = ammo_pickup_list[index]
        ammo_pickup_list[index] = [i[j] if j in i else (1 if index==1 else 0) for j in ammo_item_list]

    #[print(i) for i in ammo_pickup_list]

    drop_dict = {"MT_POSSESSED":"MT_CLIP","MT_SHOTGUY":"MT_SHOTGUN"}
                 
    
    
    file = open(path_in)
    text = file.read()
    file.close()

    path_root = ".\\"+obj_name+"\\"
    print()

    for i in range(3):
        name = ["render.lua","engine.lua","sound.lua"][i]
        file = open(path_root+name)
        code = file.read()
        file.close()

        print(name)
        code = compress(code,print_vars=i==-1,delete_newlines=i<2)
        print()
        
        find_start = ["""<c type="56"><object id="4" script='""",
                      """<c type="56"><object id="130" script='""",
                      """<c type="56"><object id="139" script='""",
                      ][i]
        find_end = ["""'>""",
                    """'>""",
                    """'>"""
                    ][i]

        start = text.find(find_start)
        end = text.find(find_end,start)
        if i==-1:
            None
            print(code.split("\n")[555-1])
            

        assert start>0 and end>0, "Code insertion search terms not in base doom file"
        
        text = text[:start+len(find_start)]+code+text[end:]
        
    
    
    
    
    
    
    
    sprites_map={}
    sprite_rotations=[]
    rotation_map={}
    new_thing = False
    
    
    for index in range(len(sprite_textures)):
        i = sprite_textures[index]

        if i[5]=="0":
            new_thing = True
            sprite_rotations.append([index+1 for j in range(8)])
        else:
            if i[5]=="1":
                sprite_rotations.append([0 for j in range(8)])
                new_thing = True
            
            sprite_rotations[-1][int(i[5])-1] = index+1
            if len(i)>6:
                sprite_rotations[-1][int(i[7])-1] = -(index+1)

        if new_thing:
            rotation_map[i[:5]] = len(sprite_rotations)
            new_thing = False
                
        if i[:3]=="STF":
            print(i)

        if (i[:4] in thing_sprites and (i[4] == "A" or True) and (i[5] in "01" or True)):
            
            cur = wad.asset_data.sprites[i][1]
            if not i[:4] in sprite_overrides:
                sprite_overrides[i[:4]]=res_scale_sprites_quality
            pixels+=(cur.get_width()*cur.get_height())
            num+=1
            #pygame.image.save(cur,"./img/"+i+".png")
    
    file = open("info_states.txt")
    info_states = file.read()
    file.close()
    for i in ["/","{","}","\t"," "]:
        info_states = info_states.replace(i,"")

    info_states = info_states.split("\n")
    info_states = [i.split(",") for i in info_states]
    info_states_zip = [*zip(*info_states)]
    info_states_processed = []
    sprite_numbering = [chr(i) for i in range(ord("A"),ord("~")+1)]

    state_actions = {'A_Explode':1,
                     'A_Look':2,
                     'A_Chase':3,
                     'A_FirePistol':4, # fist and chainsaw aren't included as they don't have muzzle flash
                     'A_FireShotgun':4,
                     'A_FireShotgun2':4,
                     'A_FireCGun':4,
                     'A_GunFlash':4,
                     'A_FirePlasma':4,
                     'A_PosAttack':10, # for simplicity they use the same index as their weapons
                     'A_SPosAttack':11,
                     'A_TroopAttack':12,
                     'A_SargAttack':14,
                     'A_SkullAttack':16,
                     'A_BruisAttack':19,
                     'A_CyberAttack':21,
                   }
    
    #print(info_states[5])
    for i in range(len(info_states)):
        state = info_states[i]
        cur = state[0][4:]
        if not cur in sprites_map:
            sprites_map[cur]=i+1

        if state[3] in state_actions:
            state[3]=state_actions[state[3]]
        else:
            state[3]=0
        
        frame = int(state[1])
        light = 1
        if int(state[1])>=(2**15)-100:
            frame-=2**15
            light=-1
        
        cur += sprite_numbering[int(frame)]
        #print(frame,state,cur)
        if cur in rotation_map:
            cur = rotation_map[cur]*light
        else:
            cur = 0

        info_states_processed.append([cur, #rotation index
                                      int(state[2]), #delay
                                      state[3], #action
                                      info_states_zip[7].index(state[4])+1, #next state
                                      0, #used for pickups
                                      ])


    file = open("info_spawn.txt")
    info_spawn = file.read()
    file.close()
    #print(info_states_processed[456])
    

    info_spawn = info_spawn.split("""
    },

""")

    spawn_flags = {'MF_NOTDMATCH':0,
                   'MF_COUNTITEM':0,
                   'MF_NOBLOCKMAP':0,
                   'MF_NOSECTOR':0,
                   'MF_SOLID':1,
                   'MF_NOGRAVITY':4,
                   'MF_DROPOFF':0,
                   'MF_FLOAT':0,
                   'MF_NOCLIP':0,
                   'MF_SPECIAL':0,
                   'MF_PICKUP':0,
                   'MF_SPAWNCEILING':0,
                   'MF_SHADOW':8,
                   'MF_NOBLOOD':0,
                   'MF_SHOOTABLE':2,
                   'MF_MISSILE':0,
                   'MF_COUNTKILL':0,
                   }
    
    for index in range(len(info_spawn)):
        i = info_spawn[index]
        cur = i.split("\n")

        
        
        for j in range(1,len(cur)):
            cur[j] = cur[j][1:]
            cur[j] = cur[j][:min(cur[j].find(",")%9999,cur[j].find("*")%9999,cur[j].find("\t")%9999)]
            try:
                cur[j] = int(cur[j])
            except:
                None

        cur[0]=cur[0][10:]
        if cur[0] in ammo_pickup_dict:
            cur.append(ammo_pickup_dict[cur[0]])
        else:
            cur.append(0)

        cur.append(0)
        cur.append(0)
        cur.append(0)
        if cur[0] in health_pickup_list_zip[0]:
            cur.append(health_pickup_list_zip[0].index(cur[0])+1)
            #print(health_pickup_list[cur[28]-1][1])
        else:
            cur.append(0)
        #print(len(cur))

        for j in [2,4,8,11,12,13,14,23]:
            if cur[j] != 0:
                cur[j] = info_states_zip[7].index(cur[j])+1

        #print(cur[0])
        #if cur[0]=="MT_TROOP":
        #    for j in range(len(cur)):
        #        print(j,cur[j])

        if cur[22] != 0:
            cur[22] = sum([spawn_flags[j] for j in cur[22].split("|")])
        
        #print(cur[17],cur[18])
        
        info_spawn[index] = cur
    info_spawn_zip = [*zip(*info_spawn)]

    for i in info_spawn:
        if i[0] in drop_dict:
            i[26] = info_spawn_zip[0].index(drop_dict[i[0]])+1
            i[27] = info_spawn[i[26]-1][2]

    for i in ammo_pickup_dict:
        cur = info_spawn[info_spawn_zip[0].index(i)]
        info_states_processed[cur[2]-1][4] = 1
            #print(i[26])

    for i in health_pickup_list_zip[0]:
        index = info_spawn[info_spawn_zip[0].index(i)][2]-1
        seen = []
        while not index in seen:
            cur = info_states_processed[index]
            cur[4] = 1
            seen.append(index)
            if cur[1]>0:
                index=cur[3]-1
            

    for i in info_spawn:
        for j in range(len(i)):
            if type(i[j]) == type(""):
                i[j] = 0

    file = open("weapon_states.txt")
    weapon_states = file.read()
    file.close()

    weapon_states = weapon_states.split("""
    },
    {
""")
    for index in range(len(weapon_states)):
        i = weapon_states[index].split("\n")
        i = [j.replace("\t","").replace(" ","").replace("/","").replace(",","") for j in i]
        for j in range(2,7):
            #print(i[j])
            i[j] = info_states_zip[7].index(i[j])+1
        i=i[2:]
        weapon_states[index]=i
        #print(i)
    
    
    
        
        

    
    #print(pixels//(8**2)/(4000/3.5),pixels,num)
    #halt

    


    #print(wall_textures)
    #halt

    for map_name_index in range(len(map_order)):
        
        map_name = map_order[map_name_index]
        level_data_offset = (map_name_index+3)*10
        
        level_wad = WADData(["wad/"+i for i in file_name], map_name=map_name,import_textures=False)


        blockmap = [level_wad.blockmap[0:4]]
        #print(blockmap)
        for i in range(4,4+level_wad.blockmap[2]*level_wad.blockmap[3]):
            index = level_wad.blockmap[i]
            cur = []
            while level_wad.blockmap[index] != 65535:
                cur.append(level_wad.blockmap[index]+1)
                index += 1
                
            if blockmap_skip_first:
                cur = cur[1:]
            blockmap.append(cur)

        for i in range(2):
            if blockmap[0][i]>2**15:
                blockmap[0][i]-=2**16

        og_blockmap = dcopy(blockmap)
        width, height = og_blockmap[0][2], og_blockmap[0][3]
        for i in range(width):       #adds neighbouring blocks into the current block
            for j in range(height):  #used since Citrus Doom only checks the block an object is in, not neighbouring ones
                curset=set()
                for k in [(0,0),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]:
                    curx = (i+k[0])%width
                    cury = (j+k[1])%height
                    curset = set.union(curset,og_blockmap[1+curx+cury*width])
                
                blockmap[1+i+j*width] = list(curset)
        
        #line_type_repleacements = {32:32-18,33:33-18,34:34-18,
        #                           26:32-18,27:34-18,28:33-18, #open often to stay open, but treated as open often
        #                           31:1,
        #                           }
                

        for index in range(len(level_wad.linedefs)):
            i=level_wad.linedefs[index]
            i.front_sidedef_id=(i.front_sidedef_id+1)%65536
            i.back_sidedef_id=(i.back_sidedef_id+1)%65536

            if i.front_sidedef_id > 0 and i.back_sidedef_id > 0:
                
                s1i=level_wad.sidedefs[i.front_sidedef_id-1].sector_id
                s2i=level_wad.sidedefs[i.back_sidedef_id-1].sector_id
                
                s1=level_wad.sectors[s1i]
                s2=level_wad.sectors[s2i]

                #if i.line_type in line_type_repleacements:
                #    i.line_type = line_type_repleacements[i.line_type]

                if s1.neighbouring_highest_ceiling == None:
                    s1.neighbouring_highest_ceiling = s2.ceil_height
                else:
                    s1.neighbouring_highest_ceiling = max(s1.neighbouring_highest_ceiling,s2.ceil_height)

                if s2.neighbouring_highest_ceiling == None:
                    s2.neighbouring_highest_ceiling = s1.ceil_height
                else:
                    s2.neighbouring_highest_ceiling = max(s2.neighbouring_highest_ceiling,s1.ceil_height)
                

                if s1.neighbouring_lowest_ceiling == None:
                    s1.neighbouring_lowest_ceiling = s2.ceil_height
                else:
                    s1.neighbouring_lowest_ceiling = min(s1.neighbouring_lowest_ceiling,s2.ceil_height)

                if s2.neighbouring_lowest_ceiling == None:
                    s2.neighbouring_lowest_ceiling = s1.ceil_height
                else:
                    s2.neighbouring_lowest_ceiling = min(s2.neighbouring_lowest_ceiling,s1.ceil_height)


                if s1.neighbouring_highest_floor == None:
                    s1.neighbouring_highest_floor = s2.floor_height
                else:
                    s1.neighbouring_highest_floor = max(s1.neighbouring_highest_floor,s2.floor_height)

                if s2.neighbouring_highest_floor == None:
                    s2.neighbouring_highest_floor = s1.floor_height
                else:
                    s2.neighbouring_highest_floor = max(s2.neighbouring_highest_floor,s1.floor_height)


                if s1.neighbouring_lowest_floor == None:
                    s1.neighbouring_lowest_floor = s2.floor_height
                else:
                    s1.neighbouring_lowest_floor = min(s1.neighbouring_lowest_floor,s2.floor_height)

                if s2.neighbouring_lowest_floor == None:
                    s2.neighbouring_lowest_floor = s1.floor_height
                else:
                    s2.neighbouring_lowest_floor = min(s2.neighbouring_lowest_floor,s1.floor_height)
            

        sector_thinkers=[] # format for thinkers is (targ sec, value to change (1 for floor, 2 for ceil), targ height, end delay, next thinker)
        nil_thinker = insert_thinker((0,0,0,0,0)) # used in activate once stuff, a target thinker is needed to stop it being deleted
        for index in range(len(level_wad.linedefs)): # compiles the sector thinkers
            i=level_wad.linedefs[index]

            s1i=level_wad.sidedefs[i.front_sidedef_id-1].sector_id
            s2i=level_wad.sidedefs[i.back_sidedef_id-1].sector_id
            
            s1=level_wad.sectors[s1i]
            s2=level_wad.sectors[s2i]
    
            if i.line_type==1:
                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.floor_height, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.neighbouring_lowest_ceiling-8, TICKRATE*4, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==2: #W1 Door Stay Open
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling-8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==5: #W1 Floor To Lowest Adjacent Ceiling
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==9: #S1 Floor Donut (not actually a donut yet)
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_lowest_floor, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==16: #W1 Door Close Then Open 30 Sec Later
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling-8, -1, nil_thinker)
                next_thinker = insert_thinker(thinker)

                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].floor_height, TICKRATE*30, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==18: #S1 Floor To Highest Adjacent Floor
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_highest_floor, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==20: #S1 Floor To Higher Floor Change Text (highest floor, no change tex)
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_highest_floor, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==22: #W1 Floor To Higher Floor Change Text (highest floor, no change tex)
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_highest_floor, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==23: #S1 Floor To Lowest Adjacent Floor
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_lowest_floor, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1
            
            elif i.line_type==26:
                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.floor_height, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.neighbouring_lowest_ceiling-8, TICKRATE*4, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=key_indexes["blue"]

            elif i.line_type==27:
                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.floor_height, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.neighbouring_lowest_ceiling-8, TICKRATE*4, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=key_indexes["yellow"]

            elif i.line_type==28:
                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.floor_height, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.neighbouring_lowest_ceiling-8, TICKRATE*4, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=key_indexes["red"]

            elif i.line_type==31:

                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.neighbouring_lowest_ceiling-8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==32:
                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.neighbouring_lowest_ceiling-8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=key_indexes["blue"]

            elif i.line_type==33:
                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.neighbouring_lowest_ceiling-8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=key_indexes["red"]

            elif i.line_type==34:
                thinker = (level_wad.sidedefs[i.back_sidedef_id-1].sector_id+1, 2, s2.neighbouring_lowest_ceiling-8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=key_indexes["yellow"]

            elif i.line_type==36: #W1 Floor To 8 Above Heighest Adjacent Floor Fast (not fast)
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_highest_floor+8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==38: #W1 Floor To Lowest Adjacent Floor
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_lowest_floor, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==46: #GR Door (not gun activated)
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].floor_height, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling-8, TICKRATE*4, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==62: #SR Lift
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].floor_height, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_lowest_floor, TICKRATE*3, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==63: #SR Door
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].floor_height, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling-8, TICKRATE*4, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==70: #SR Floor To 8 Above Heighest Adjacent Floor Fast (not fast)
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_highest_floor+8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==76: #WR Door Close Then Open 30 Sec Later
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling-8, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].floor_height, TICKRATE*30, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==82: #WR Floor To Lowest Adjacent Floor
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_lowest_floor, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==86: #WR Door Stay Open
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling-8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==88: #WR Lift Also Monsters (not monsters)
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].floor_height, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_lowest_floor, TICKRATE*3, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==90: #WR Door
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].floor_height, 1, 0)
                next_thinker = insert_thinker(thinker)

                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling-8, TICKRATE*4, next_thinker)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==91: #WR Floor To Lowest Adjacent Ceiling
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==98: #WR Floor To 8 Above Heighest Adjacent Floor Fast (not fast)
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 1, level_wad.sectors[cur_sec-1].neighbouring_highest_floor+8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif i.line_type==103: #S1 Door Stay Open
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)

                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling-8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=1

            elif i.line_type==109: #W1 Door Stay Open Fast (not fast)
                cur_sec = find_sector(i.sector_tag)
                assert cur_sec != 0, "No sector has the tag "+str(i.sector_tag)+" used by linedef "+str(index)
                
                thinker = (cur_sec, 2, level_wad.sectors[cur_sec-1].neighbouring_lowest_ceiling-8, 1, 0)
                i.thinker_id = insert_thinker(thinker)

                i.line_type=2

            elif 0<i.line_type<3000 and not i.line_type in [11,#normal exit
                                                            35,#set light level
                                                            48,#moving texture
                                                            51,#secret exit
                                                            97,#teleport
                                                            ]:
                print("unknown linedef type",i.line_type,"in level",map_name)

            
        
                
        
        cur=""
        curnum=0
        
        for index in range(len(level_wad.things)):
            i=level_wad.things[index]
            
            
            if i.type in info_spawn_zip[1] and i.flags&16==0:
                begining = info_spawn_zip[1].index(i.type)+1
                state = info_spawn_zip[2][begining-1]

                curnum+=1
                #print(state,len(sprite_textures))
            
                new=(str([i.pos[0],i.pos[1],i.angle,begining,i.flags,state])[1:-1]+",").replace(" ","")
                if len(cur)+len(new)>curmax:
                    packets.append(str(level_data_offset+1)+",6,"+str(curnum-1)+","+cur[:-1])
                    cur = new
                    curnum = 1
                else:
                    cur += new
        
        packets.append(str(level_data_offset+1)+",6,"+str(curnum)+","+cur[:-1])



        
        cur=""
        curnum=0 
        for index in range(len(level_wad.linedefs)):
            i=level_wad.linedefs[index]
            
            curnum+=1
            #[start_vert,end_vert,flag,type,tag,front_sidedef,back_sidedef,floor_height,ceil_height]
            #if (i.flags & 4 == 0):
            #    temp=((i.back_sidedef_id+1)%65536)+((i.front_sidedef_id+1)%65536)
            #    temp=level_wad.sidedefs[temp-1]
            #    print(index,temp.lower_texture,temp.upper_texture)

            
            
                
            
            new=(str([i.start_vertex_id+1,i.end_vertex_id+1,i.flags,i.line_type,i.thinker_id,i.front_sidedef_id,i.back_sidedef_id])[1:-1]+",").replace(" ","")
            if len(cur)+len(new)>curmax:
                packets.append(str(level_data_offset+2)+",7,"+str(curnum-1)+","+cur[:-1])
                cur = new
                curnum = 1
            else:
                cur += new
                
        packets.append(str(level_data_offset+2)+",7,"+str(curnum)+","+cur[:-1])

        cur=""
        curnum=0 
        for index in range(len(level_wad.sidedefs)):
            i=level_wad.sidedefs[index]
            
            curnum+=1
            
            new=(str([i.x_offset,i.y_offset,wall_looker.index(i.upper_texture),wall_looker.index(i.lower_texture),wall_looker.index(i.middle_texture),i.sector_id+1])[1:-1]+",").replace(" ","")
            if len(cur)+len(new)>curmax:
                packets.append(str(level_data_offset+3)+",6,"+str(curnum-1)+","+cur[:-1])
                cur = new
                curnum = 1
            else:
                cur += new

        packets.append(str(level_data_offset+3)+",6,"+str(curnum)+","+cur[:-1])

        
        cur=""
        curnum=0 
        for index in range(len(level_wad.vertexes)):
            i=level_wad.vertexes[index]

            curnum+=1
            
            new=(str(i)[1:-1]+",").replace(" ","")
            if len(cur)+len(new)>curmax:
                packets.append(str(level_data_offset+4)+",2,"+str(curnum-1)+","+cur[:-1])
                cur = new
                curnum = 1
            else:
                cur += new
                
        packets.append(str(level_data_offset+4)+",2,"+str(curnum)+","+cur[:-1])


        cur=""
        curnum=0 
        for index in range(len(level_wad.segments)):
            i=level_wad.segments[index]
            
            curnum+=1
            
            new=(str([i.start_vertex_id+1,i.end_vertex_id+1,round(i.angle),i.linedef_id+1,i.direction,i.offset])[1:-1]+",").replace(" ","")
            if len(cur)+len(new)>curmax:
                packets.append(str(level_data_offset+5)+",6,"+str(curnum-1)+","+cur[:-1])
                cur = new
                curnum = 1
            else:
                cur += new
                
        packets.append(str(level_data_offset+5)+",6,"+str(curnum)+","+cur[:-1])

        
        cur=""
        curnum=0 
        for index in range(len(level_wad.sub_sectors)):
            i=level_wad.sub_sectors[index]
            
            curnum+=1
            
            new=(str([i.seg_count,round(i.first_seg_id+1)])[1:-1]+",").replace(" ","")
            if len(cur)+len(new)>curmax:
                packets.append(str(level_data_offset+6)+",2,"+str(curnum-1)+","+cur[:-1])
                cur = new
                curnum = 1
            else:
                cur += new
                
        packets.append(str(level_data_offset+6)+",2,"+str(curnum)+","+cur[:-1])

        
        cur=""
        curnum=0 
        for index in range(len(level_wad.nodes)):
            i=level_wad.nodes[index]
            
            curnum+=1
            
            new=(str([i.x_partition,i.y_partition,i.dx_partition,i.dy_partition,0,0,i.front_child_id+1,i.back_child_id+1])[1:-1]+",").replace(" ","")
            if len(cur)+len(new)>curmax:
                packets.append(str(level_data_offset+7)+",8,"+str(curnum-1)+","+cur[:-1])
                cur = new
                curnum = 1
            else:
                cur += new
                
        packets.append(str(level_data_offset+7)+",8,"+str(curnum)+","+cur[:-1])
        #print(level_wad.asset_data.sky_id)
        #halt
        
        cur=""
        curnum=0 
        for index in range(len(level_wad.sectors)):
            i=level_wad.sectors[index]
            
            curnum+=1
            
            if i.ceil_texture != wad.asset_data.sky_id:
                cur_ceil = flat_looker.index(i.ceil_texture)
            else:
                cur_ceil = 0

            if i.floor_texture != wad.asset_data.sky_id:
                cur_floor = flat_looker.index(i.floor_texture)
            else:
                cur_floor = 0

            #[floor_h, ceil_h, floor_t, ceil_t, light, type, tag, refresh, surrounding_ceil_h, stage, timer]
            
            new=(str([i.floor_height,i.ceil_height,cur_floor,cur_ceil,i.light_level,i.type,i.tag])[1:-1]+",").replace(" ","")
            if len(cur)+len(new)>curmax:
                packets.append(str(level_data_offset+8)+",7,"+str(curnum-1)+","+cur[:-1])
                cur = new
                curnum = 1
            else:
                cur += new
                
        packets.append(str(level_data_offset+8)+",7,"+str(curnum)+","+cur[:-1])


        cur=""
        curnum=0 
        for i in sector_thinkers:

            curnum+=1
            #print(len(i))
            new=(str(i)[1:-1]+",").replace(" ","")
            if len(cur)+len(new)>curmax:
                packets.append(str(level_data_offset+9)+",5,"+str(curnum-1)+","+cur[:-1])
                cur = new
                curnum = 1
            else:
                cur += new

        if cur!="":
            packets.append(str(level_data_offset+9)+",5,"+str(curnum)+","+cur[:-1])


        cur=""
        curnum=0
        curlen=len(blockmap[0])
        #print(blockmap)
        #halt
        for index in range(len(blockmap)):
            i=blockmap[index]
            
            curnum+=1

            if len(i)>0:
                new=(str(i)[1:-1]+",").replace(" ","")
            else:
                new=""
            
            if len(cur)+len(new)>curmax or len(i)!=curlen:
                maybe_packet = str(level_data_offset+10)+","+str(curlen)+","+str(curnum-1)+","+cur[:-1]
                if cur=="":
                    maybe_packet = maybe_packet[:-1]
                if len(maybe_packet)+len(packets[-1])+1 <= curmax:
                    packets[-1] += (","+maybe_packet)
                else:
                    packets.append(maybe_packet)
                cur = new
                curnum = 1
                curlen=len(i)
            else:
                cur += new

        maybe_packet = str(level_data_offset+10)+","+str(curlen)+","+str(curnum)+","+cur[:-1]
        if cur=="":
            maybe_packet = maybe_packet[:-1]
        packets.append(maybe_packet)

    print(len(packets), "text boxes of level data")


    cur=""
    curnum=0 
    for index in range(len(health_pickup_list)):
        i=health_pickup_list[index][1]
        curnum+=1
        
        new=(str(i)[1:-1]+",").replace(" ","")
        if len(cur)+len(new)>curmax:
            packets.append("11,"+str(len(i))+","+str(curnum-1)+","+cur[:-1])
            cur = new
            curnum = 1
        else:
            cur += new
    packets.append("11,"+str(len(i))+","+str(curnum)+","+cur[:-1])
    
    
    cur=""
    curnum=0 
    for index in range(len(ammo_pickup_list)):
        i=ammo_pickup_list[index]
        curnum+=1
        
        new=(str(i)[1:-1]+",").replace(" ","")
        if len(cur)+len(new)>curmax:
            packets.append("12,"+str(len(i))+","+str(curnum-1)+","+cur[:-1])
            cur = new
            curnum = 1
        else:
            cur += new
    packets.append("12,"+str(len(i))+","+str(curnum)+","+cur[:-1])


    file = open("random.txt")
    random = file.read()
    file.close()

    random = random.split("\n")
    cur = "13,256,1"
    for i in random:
        i = i.split(" ")
        cur += (","+i[1])

    if len(packets[-1])+len(cur)+1 <= curmax:
        packets[-1]+=(","+cur)
    else:
        packets.append(cur)

    file = open("fuzz.txt")
    fuzz = file.read()
    file.close()

    fuzz = fuzz.replace("\n    ","")

    fuzz = fuzz.split(",")
    cur = "13,50,1"
    darkness = 1
    for i in fuzz:
        if not "-" in i:
            darkness = 1
        cur += (","+str(darkness))
        darkness += 1
    #print(cur)

    if len(packets[-1])+len(cur)+1 <= curmax:
        packets[-1]+=(","+cur)
    else:
        packets.append(cur)
    

    file = open("weapons.txt")
    weapons = file.read()
    file.close()
    weapons = weapons.split("\n")
    weapons = [i.split("\t") for i in weapons]
    cur=""
    curnum=0
    curlen=len(weapons[0])-1
    #print(blockmap)
    #halt
    for index in range(len(weapons)):
        i=weapons[index]
        
        curnum+=1

        
        new = i[1:]
        
        if new[7]!="0":
            #print(temp,info_spawn_zip[0])
            #print(new[7])
            temp = info_spawn_zip[0].index(new[7])
            temp_spawn = info_spawn[temp]
            if int(new[6])>0:
                new[5]=temp_spawn[16]
                #print(new[6])
            for k in [2,13]:
                
                temp_sprite = info_states_processed[temp_spawn[k]-1][0]
                if temp_sprite != 0:
                    sprite_name = sprite_textures[abs(temp_sprite)-1][:4]
                    
                    if not sprite_name in sprite_overrides:
                        sprite_overrides[sprite_name] = res_scale_sprites_projectiles
            new[7] = temp+1


        #if new[12] in sprite_textures:
        #    if not new[12] in sprite_overrides:
        #        sprite_overrides[new[12]] = res_scale_sprites_weapons
        #    new[12] = sprite_textures.index(new[12])+1
        #else:
        #    new[12] = 0
        
        for j in range(len(new)):
            if type(new[j]) != type(""):
                None
            elif new[j].count(".")>0:
                new[j] = float(new[j])
            else:
                new[j] = int(new[j])
        #print(new)
        #halt
       
        new=(str(new)[1:-1]+",").replace(" ","")
        if len(cur)+len(new)>curmax:
            packets.append("15,"+str(curlen)+","+str(curnum-1)+","+cur[:-1])
            cur = new
            curnum = 1
        else:
            cur += new
            
    packets.append("14,"+str(curlen)+","+str(curnum)+","+cur[:-1])

    ""
    cur=""
    curnum=0 
    for index in range(len(info_spawn)):
        i=info_spawn[index]
        curnum+=1
        
        new=(str(i)[1:-1]+",").replace(" ","")
        if len(cur)+len(new)>curmax:
            packets.append("15,"+str(len(i))+","+str(curnum-1)+","+cur[:-1])
            cur = new
            curnum = 1
        else:
            cur += new
    packets.append("15,"+str(len(i))+","+str(curnum)+","+cur[:-1])

    
    cur=""
    curnum=0 
    for index in range(len(info_states_processed)):
        i=info_states_processed[index]
        if len(i) != 5:
            print(i)
            halt

        curnum+=1
        
        new=(str(i)[1:-1]+",").replace(" ","")
        if len(cur)+len(new)>curmax:
            packets.append("16,5,"+str(curnum-1)+","+cur[:-1])
            cur = new
            curnum = 1
        else:
            cur += new
    packets.append("16,5,"+str(curnum)+","+cur[:-1])
    
    
    cur=""
    curnum=0 
    for index in range(len(sprite_rotations)):
        i=sprite_rotations[index]
        
        curnum+=1
        
        new=(str(i)[1:-1]+",").replace(" ","")
        if len(cur)+len(new)>curmax:
            packets.append("17,8,"+str(curnum-1)+","+cur[:-1])
            cur = new
            curnum = 1
        else:
            cur += new
            
    packets.append("17,8,"+str(curnum)+","+cur[:-1])


    for index in wad.sounds:
        i=wad.sounds[index]
        
        new="18,"+str(len(i))+",1,"+((str(i)[1:-1]).replace(" ",""))
        #print(new)
        if len(new)+len(packets[-1])+1>curmax:
            packets.append(new)
        else:
            packets[-1]+=(","+new)
    

    misc_additions = [[1,2,9,6,11,12,19,3],
                      [0,45,-45,90,-90],
                      [all_sprite_textures.index("STFST01")+1,],
                      [0,0,7,8,0,1,2,9,3],
                      [0,0,255],
                      [255,0,0],
                      [200,200,0],
                      ]
    for index in range(len(misc_additions)):
        i=misc_additions[index]
        
        new="19,"+str(len(i))+",1,"+((str(i)[1:-1]).replace(" ",""))
        #print(new)
        if len(new)+len(packets[-1])+1>curmax:
            packets.append(new)
        else:
            packets[-1]+=(","+new)

    
    cur=""
    curnum=0 
    for index in range(len(weapon_states)):
        i=weapon_states[index]
        
        curnum+=1
        
        new=(str(i)[1:-1]+",").replace(" ","")
        if len(cur)+len(new)>curmax:
            packets.append("29,5,"+str(curnum-1)+","+cur[:-1])
            cur = new
            curnum = 1
        else:
            cur += new
            
    packets.append("29,5,"+str(curnum)+","+cur[:-1])
    
    

    #print(sprite_overrides)

    checksum = str(wall_overrides)+str(sprite_overrides)
    checksum += str(res_scale_walls)+str(res_scale_flats)+str(res_scale_sprites)+str(res_scale_sky)+str(file_name)
    
    try:
        file = open("cache.txt")
        cache = json.load(file)
        file.close()
        last_checksum = cache[0]
    except:
        last_checksum = ""

    if last_checksum != checksum or force_new_cache:
        print("cache invalid, regenerating cache...")
        
        colourmap=[]
        colourmap_useage=[]
        temp_packets=[]

        i=orange
        width=i.get_width()
        height=i.get_height()

        av=(0,0,0)
        av_num=0
        
        for j in range(width):
            for k in range(height):

                colour=i.get_at((j,k))
                colour=colour[:3]
                av=add(av,colour)
                av_num+=1
                if colour != trans_colour:
                    if not (colour in colourmap):
                        colourmap.append(colour)
                        colourmap_useage.append(1)
                    else:
                        colourmap_useage[colourmap.index(colour)] += 1
        av=div(av,av_num)
        
        av=tuple([flr(i) for i in av])
        if not (av in colourmap):
            colourmap.append(av)
            colourmap_useage.append(1)
        else:
            colourmap_useage[colourmap.index(av)] += 1

        orange_av=colourmap.index(av)
        

        for index in wall_textures:
            if index in wall_overrides:
                res_scale_cur = wall_overrides[index]
            else:
                res_scale_cur = res_scale_walls

            
            i=wad.asset_data.wall_textures[index]
            width=len(i)//res_scale_cur
            height=len(i[0])//res_scale_cur

            av=(0,0,0)
            av_num=0
            
            for j in range(width):
                for k in range(height):
                    colour=tuple(i[j*res_scale_cur][k*res_scale_cur])
                    if colour != trans_colour:
                        av=add(av,colour)
                        av_num+=1
                        if not (colour in colourmap):
                            colourmap.append(colour)
                            colourmap_useage.append(1)
                        else:
                            colourmap_useage[colourmap.index(colour)] += 1
            av=div(av,av_num)
            
            av=tuple([flr(i) for i in av])
            if not (av in colourmap):
                colourmap.append(av)
                colourmap_useage.append(1)
            else:
                colourmap_useage[colourmap.index(av)] += 1

            wall_avs[index]=colourmap.index(av)

        for index in flat_textures:
            i=wad.asset_data.flat_textures[index]
            width=len(i)//res_scale_flats
            height=len(i[0])//res_scale_flats

            av=(0,0,0)
            av_num=0
            
            for j in range(width):
                for k in range(height):
                    colour=tuple(i[j*res_scale_flats][k*res_scale_flats])
                    av=add(av,colour)
                    av_num+=1
                    if not (colour in colourmap):
                        colourmap.append(colour)
                        colourmap_useage.append(1)
                    else:
                        colourmap_useage[colourmap.index(colour)] += 1
            av=div(av,av_num)
            
            av=tuple([flr(i) for i in av])
            if not (av in colourmap):
                colourmap.append(av)
                colourmap_useage.append(1)
            else:
                colourmap_useage[colourmap.index(av)] += 1

            flat_avs[index]=colourmap.index(av)

        for index in all_sprite_textures:
            if index in sprite_overrides:
                res_scale_cur = sprite_overrides[index]
            elif index[:4] in sprite_overrides:
                res_scale_cur = sprite_overrides[index[:4]]
            else:
                res_scale_cur = res_scale_sprites
                
            i=all_sprites[index][1]
            width=i.get_width()//res_scale_cur
            height=i.get_height()//res_scale_cur

            av=(0,0,0)
            av_num=0
            
            for j in range(width):
                for k in range(height):
                    
                    colour=i.get_at((j*res_scale_cur,k*res_scale_cur))
                    colour=colour[:3]
                    if colour != trans_colour:
                        av=add(av,colour)
                        av_num+=1
                        if not (colour in colourmap):
                            colourmap.append(colour)
                            colourmap_useage.append(1)
                        else:
                            colourmap_useage[colourmap.index(colour)] += 1
            if av_num != 0:
                av=div(av,av_num)
            
            av=tuple([flr(i) for i in av])
            if not (av in colourmap):
                colourmap.append(av)
                colourmap_useage.append(1)
            else:
                colourmap_useage[colourmap.index(av)] += 1

            sprite_avs[index]=colourmap.index(av)
            

        

        i=wad.asset_data.sky_tex
        width=len(i)//res_scale_sky
        height=len(i[0])//res_scale_sky

        av=(0,0,0)
        av_num=0
        
        for j in range(width):
            for k in range(height):

                colour=tuple(i[j*res_scale_sky][k*res_scale_sky])
                av=add(av,colour)
                av_num+=1
                if not (colour in colourmap):
                    colourmap.append(colour)
                    colourmap_useage.append(1)
                else:
                    colourmap_useage[colourmap.index(colour)] += 1
        av=div(av,av_num)
        
        av=tuple([flr(i) for i in av])
        if not (av in colourmap):
            colourmap.append(av)
            colourmap_useage.append(1)
        else:
            colourmap_useage[colourmap.index(av)] += 1

        sky_av=colourmap.index(av)

        

        colourmap = [*zip(colourmap_useage,colourmap,[*range(len(colourmap))])]
        colourmap.sort(reverse=True) # more frequently used colours get priory, as smaller numbers take up less space
        colourmap = [[colourmap[j][i] for j in range(len(colourmap))] for i in range(len(colourmap[0]))]
        
        for i in wall_avs:
            wall_avs[i] = colourmap[2].index(wall_avs[i])
        for i in flat_avs:
            flat_avs[i] = colourmap[2].index(flat_avs[i])
        for i in sprite_avs:
            sprite_avs[i] = colourmap[2].index(sprite_avs[i])
        
        sky_av = colourmap[2].index(sky_av)
        colourmap = colourmap[1]

        print("colourmap complete")

        print(len(colourmap),"colours")
        
            
        cur=""
        curnum=0 
        for index in range(len(colourmap)):
            i=sq(colourmap[index])
            
            curnum+=1
            
            new=(str(i)[1:-1]+",").replace(" ","")
            if len(cur)+len(new)>curmax:
                temp_packets.append("20,3,"+str(curnum-1)+","+cur[:-1])
                cur = new
                curnum = 1
            else:
                cur += new

        temp_packets.append("20,3,"+str(curnum)+","+cur[:-1])


                
        

        

        t=0
        i=orange
        width=i.get_width()
        height=i.get_height()
        cur="25,"+str(width*height+4)+",1,"+str(width)+","+str(height)+","+str(1)+","+str(orange_av)

        if len(temp_packets[-1])+len(cur)+1 <= curmax:
            temp_packets[-1]+=(","+cur)
        else:
            temp_packets.append(cur)
            t+=1
        
        for j in range(width):
            for k in range(height):
                colour=i.get_at((j,k))
                colour=colour[:3]
                if colour != trans_colour:
                    cur = str(colourmap.index(colour)+1)
                else:
                    cur = "0"
                
                if len(temp_packets[-1])+len(cur)+1 <= curmax:
                    temp_packets[-1]+=(","+cur)
                else:
                    temp_packets.append(cur)
                    t+=1
        
        print(t, "text boxes of orange")
        
        t=0
        for index in wall_textures:
            if index in wall_overrides:
                res_scale_cur = wall_overrides[index]
            else:
                res_scale_cur = res_scale_walls
                
            i=wad.asset_data.wall_textures[index]
            switch=(str(wall_textures.index("SW2"+index[3:])+1) if index[0:3]=="SW1" else "0")
            width=len(i)//res_scale_cur
            height=len(i[0])//res_scale_cur
            cur = "21,"+str(width*height+5)+",1,"+str(width)+","+str(height)+","
            cur+= str(res_scale_cur)+","+switch+","+str(wall_avs[index]+1)

            if len(temp_packets)==0:
                temp_packets.append(cur)
            elif len(temp_packets[-1])+len(cur)+1 <= curmax:
                temp_packets[-1]+=(","+cur)
            else:
                temp_packets.append(cur)
                t+=1
            
            for j in range(width):
                for k in range(height):
                    colour=tuple(i[j*res_scale_cur][k*res_scale_cur])
                    if colour != trans_colour:
                        cur = str(colourmap.index(colour)+1)
                    else:
                        cur = "0"
                    
                    if len(temp_packets[-1])+len(cur)+1 <= curmax:
                        temp_packets[-1]+=(","+cur)
                    else:
                        temp_packets.append(cur)
                        t+=1
        
        print(t, "text boxes of wall textures")
        
        t=0
        for index in flat_textures:
                
            i=wad.asset_data.flat_textures[index]
            width=len(i)//res_scale_flats
            height=len(i[0])//res_scale_flats
            cur="22,"+str(width*height+4)+",1,"+str(width)+","+str(height)+","+str(res_scale_flats)+","+str(flat_avs[index]+1)

            if len(temp_packets[-1])+len(cur)+1 <= curmax:
                temp_packets[-1]+=(","+cur)
            else:
                temp_packets.append(cur)
                t+=1
            
            for j in range(width):
                for k in range(height):
                    colour=tuple(i[j*res_scale_flats][k*res_scale_flats])
                    if colour != trans_colour:
                        cur = str(colourmap.index(colour)+1)
                    else:
                        cur = "0"
                    
                    if len(temp_packets[-1])+len(cur)+1 <= curmax:
                        temp_packets[-1]+=(","+cur)
                    else:
                        temp_packets.append(cur)
                        t+=1

        print(t, "text boxes of flat textures")
        
        t=0
        for index in all_sprite_textures:
            if index in sprite_overrides:
                res_scale_cur = sprite_overrides[index]
            elif index[:4] in sprite_overrides:
                res_scale_cur = sprite_overrides[index[:4]]
            else:
                res_scale_cur = res_scale_sprites
                
            i=all_sprites[index][1]
            header=all_sprites[index][0]

            
            width=i.get_width()//res_scale_cur
            height=i.get_height()//res_scale_cur
            cur = "23,"+str(width*height+6)+",1,"+str(width)+","+str(height)+","+str(res_scale_cur)+","
            cur+= str(header.left_offset)+","+str(header.top_offset)+","+str(sprite_avs[index]+1)
            
            #if index=="TROOH5" or True:
            #    #print(header.left_offset,header.top_offset)
            #    print(res_scale_cur,(width,height),(i.get_width(),i.get_height()),(header.width,header.height))
            
            if len(temp_packets[-1])+len(cur)+1 <= curmax:
                temp_packets[-1]+=(","+cur)
            else:
                temp_packets.append(cur)
                t+=1
            
            for j in range(width):
                for k in range(height):
                    colour=i.get_at((j*res_scale_cur,k*res_scale_cur))
                    colour=colour[:3]
                    if colour != trans_colour:
                        cur = str(colourmap.index(colour)+1)
                    else:
                        cur = "0"
                    
                    if len(temp_packets[-1])+len(cur)+1 <= curmax:
                        temp_packets[-1]+=(","+cur)
                    else:
                        temp_packets.append(cur)
                        t+=1

        print(t, "text boxes of sprite textures")
        
        t=0
        i=wad.asset_data.sky_tex
        width=len(i)//res_scale_sky
        height=len(i[0])//res_scale_sky-(8//res_scale_sky)#bottom pixels are just purple
        cur="24,"+str(width*height+4)+",1,"+str(width)+","+str(height)+","+str(res_scale_sky)+","+str(sky_av)

        if len(temp_packets[-1])+len(cur)+1 <= curmax:
            temp_packets[-1]+=(","+cur)
        else:
            temp_packets.append(cur)
            t+=1
        
        for j in range(width):
            for k in range(height):
                colour=tuple(i[j*res_scale_sky][k*res_scale_sky])
                cur = str(colourmap.index(colour)+1)
                
                if len(temp_packets[-1])+len(cur)+1 <= curmax:
                    temp_packets[-1]+=(","+cur)
                else:
                    temp_packets.append(cur)
                    t+=1
        
        print(t, "text boxes of sky textures")
        
            

        #halt

        
                
        
        cache = [checksum,temp_packets]

        
        
        file = open("cache.txt",mode="w", newline='\n')
        json.dump(cache,file)
        file.close()
        print("textures cached")

    packets = cache[1] + packets

    
    parts = packets
    print(len(parts),"text boxes total")
    sizes = [len(i) for i in packets]
    print("largest text box is",max(sizes))
    print("average text box is",sum(sizes)/len(sizes))
    
    #[(print(i) if (len(i)==largest) else 0) for i in packets]
    
    

    text_block= ['''<c type="58"><object id="85" n="''',
                 '''" v="''',
                 '''"><pos x="-8.25" y="''',
                 '''"/></object></c>''']
    contents = ""
    
    
    for i in range(len(parts)):
        contents += (text_block[0]+str(i+1)+text_block[1]+parts[i]+text_block[2]+str((i+1)*0.5)+text_block[3])

    

    

    find_start1 = '''<c type="58"><object id="84" n="text block start"><pos x="-8.25"/></object></c>'''
    find_end1 = '''<c type="57">'''

    
    start1 = text.find(find_start1)
    end1 = text.find(find_end1)
    text = text[:start1+len(find_start1)]+contents+text[end1:]

    
    
    file = open(path_out,mode="w", newline='\n')
    file.write(text)
    file.close()

    print("took",time.time()-start_time,"seconds")
    
    
