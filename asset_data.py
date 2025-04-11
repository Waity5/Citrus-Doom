from settings import *
from data_types import PatchHeader
import pygame as pg

def off_add(a,b):
    return (a[0],a[1]+b)

class Patch:
    def __init__(self, asset_data, name, is_sprite=True):
        self.asset_data = asset_data
        self.name = name
        #
        self.palette = asset_data.palette
        self.header, self.patch_columns = self.load_patch_columns(name)
        self.width = self.header.width
        self.height = self.header.height
        #
        self.image = self.get_image()
        if is_sprite:
            self.image = [self.header,pg.transform.scale(self.image, (
                self.width, self.height)
                )]

    def load_patch_columns(self, patch_name):
        reader = self.asset_data.reader
        patch_index = self.asset_data.get_lump_index(patch_name)
        patch_offset = reader.directory[patch_index]['lump_offset']
        #
        patch_header = self.asset_data.reader.read_patch_header(patch_offset)
        patch_columns = []

        for i in range(patch_header.width):
            offs = off_add(patch_offset,patch_header.column_offset[i])
            while True:
                patch_column, offs = reader.read_patch_column(offs)
                patch_columns.append(patch_column)
                if patch_column.top_delta == 0xFF:
                    break
        return patch_header, patch_columns

    def get_image(self):
        image = pg.Surface([self.width, self.height])
        image.fill(COLOR_KEY)
        image.set_colorkey(COLOR_KEY)

        ix = 0
        for column in self.patch_columns:
            if column.top_delta == 0xFF:
                ix += 1
                continue

            for iy in range(column.length):
                color_idx = column.data[iy]
                color = self.palette[color_idx]
                image.set_at([ix, iy + column.top_delta], color)

        return image


class Texture:
    def __init__(self, asset_data, tex_map):
        self.asset_data = asset_data
        self.tex_map = tex_map
        self.image = self.get_image()

    def get_image(self):
        image = pg.Surface([self.tex_map.width, self.tex_map.height])
        image.fill(COLOR_KEY)
        image.set_colorkey(COLOR_KEY)
        #
        for patch_map in self.tex_map.patch_maps:
            patch = self.asset_data.texture_patches[patch_map.p_name_index]
            image.blit(patch.image, (patch_map.x_offset, patch_map.y_offset))
        # --------------------------------- #
        image = pg.surfarray.array3d(image)
        # --------------------------------- #
        return image


# ---------------------------------------------------- #
class Flat:
    def __init__(self, asset_data, flat_data):
        self.flat_data = flat_data
        self.palette = asset_data.palette
        self.image = self.get_image()

    def get_image(self):
        image = pg.Surface([64, 64])
        #
        for i, color_idx in enumerate(self.flat_data):
            ix = i % 64
            iy = i // 64
            color = self.palette[color_idx]
            image.set_at([ix, iy], color)
        # --------------------------------- #
        image = pg.surfarray.array3d(image)
        # --------------------------------- #
        return image
# --------------------------------------------------- #


class AssetData:
    def __init__(self, wad_data):
        self.wad_data = wad_data
        self.reader = wad_data.reader
        self.get_lump_index = wad_data.get_lump_index

        # palettes
        self.palettes = self.wad_data.get_lump_data(
            reader_func=self.reader.read_palette,
            lump_index=self.get_lump_index('PLAYPAL'),
            num_bytes=256 * 3
        )
        # current palette
        self.palette_idx = 0
        self.palette = self.palettes[self.palette_idx]

        # sprites
        self.sprites = self.get_sprites(start_marker='S_START', end_marker='S_END')

        self.face = self.get_sprites(start_marker='STFST01', end_marker='STFDEAD0', off=1)

        # texture patch names
        self.p_names = self.wad_data.get_lump_data(
            self.reader.read_string,
            self.get_lump_index('PNAMES'),
            num_bytes=8,
            header_length=4
        )

        # texture patches
        self.texture_patches = [
            Patch(self, p_name, is_sprite=False) for p_name in self.p_names
        ]

        # wall textures
        texture_maps = self.load_texture_maps(texture_lump_name='TEXTURE1')
        if self.get_lump_index('TEXTURE2'):
            texture_maps += self.load_texture_maps(texture_lump_name='TEXTURE2')

        self.load_sound("DPFIRSHT")

        self.wall_textures = {
            tex_map.name: Texture(self, tex_map).image for tex_map in texture_maps
        }
        # flat textures
        self.flat_textures = self.get_flats()

        # --------------------------------------------------------------------------- #
        # sky
        self.sky_id = 'F_SKY1'
        self.sky_tex_name = 'SKY1'
        self.sky_tex = self.wall_textures[self.sky_tex_name]
        # --------------------------------------------------------------------------- #

    def get_flats(self, start_marker='F_START', end_marker='F_END'):
        idx1 = self.get_lump_index(start_marker)
        flats = {}
        while idx1:
            idx1 += 1
            idx2 = self.get_lump_index(end_marker,start=idx1)
            flat_lumps = self.reader.directory[idx1: idx2]

            for flat_lump in flat_lumps:
                offset = flat_lump['lump_offset']
                size = flat_lump['lump_size']  # 64 x 64

                flat_data = []
                for i in range(size):
                    flat_data.append(self.reader.read_1_byte(off_add(offset,i), byte_format='B'))

                flat_name = flat_lump['lump_name']
                if not flat_name in flats:
                    flats[flat_name] = Flat(self, flat_data).image
            idx1 = self.get_lump_index(start_marker,start=idx1)
        return flats
    # --------------------------------------------------------------------------- #

    def load_texture_maps(self, texture_lump_name):
        texture_maps = []
        for addon in " 0123456789F": #jank, should be fixed later
            if addon == " ":
                addon = ""

            cur_name = texture_lump_name[0]+addon+texture_lump_name[1:]
        
            tex_idx = self.get_lump_index(cur_name,start=0)
            while tex_idx:
                offset = self.reader.directory[tex_idx]['lump_offset']

                texture_header = self.reader.read_texture_header(offset)

                for i in range(texture_header.texture_count):
                    tex_map = self.reader.read_texture_map(
                        off_add(offset,texture_header.texture_data_offset[i])
                    )
                    texture_maps.append(tex_map)

                tex_idx = self.get_lump_index(cur_name,start=tex_idx+1)
        return texture_maps

    def load_sound(self, sound_name):
        tex_idx = self.get_lump_index(sound_name)
        offset = self.reader.directory[tex_idx]['lump_offset']

        sound = self.reader.read_sound_map(offset)

        #print(sound)

        #sound = []
        #for i in range(sound_header.sample_count)
        return sound

        

        

    def get_sprites(self, start_marker='S_START', end_marker='S_END', off=0):
        idx1 = self.get_lump_index(start_marker) + 1 - off
        idx2 = self.get_lump_index(end_marker) + off
        lumps_info = self.reader.directory[idx1: idx2]
        sprites = {
            lump['lump_name']: Patch(self, lump['lump_name']).image for lump in lumps_info
        }
        return sprites
