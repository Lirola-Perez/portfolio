 #################################

def get_type_property_(self):
    values = []
    for obj in self.objects:
        if isinstance(self.current_property,list):
            value = [getattr(obj, p, None) for p in self.current_property]
            values.append(value)
        else:
            values.append(getattr(obj, self.current_property, None))
    return values

def assign_to_objects(self,val):
    for obj in self.objects:
        if isinstance(self.current_property,str) and isinstance(val,str | int):
            setattr(obj,self.current_property, val)
        elif isinstance(self.current_property, list) and isinstance(val,list):
            for num,p in enumerate(self.current_property):
                setattr(obj,p,val[num])
    return self.idf

def get_target(self,type,property):
    return getattr(self.idf.idfobjects,property,None)

# def assign_to_idf(self,id:str, val:list|str|float):
#     for obj in self.objects:
#         if obj[:] == id:
#             if isinstance(val,list):
#                 for v in val:
#                     if isinstance(self.current_property,str):
#                         setattr(obj,self.current_property,v)




# def get_info_eppy(self):
#     zones = self.idf.idfobjects['ZONE']
#     for zone in zones:
#         print(f"Zone Name: {zone.Name}")
#         print(f"  - Ceiling Height: {zone.Ceiling_Height}")
#         print(f"  - Volume: {zone.Volume}")
#     surfaces = self.idf.idfobjects['BUILDINGSURFACE:DETAILED']
#     total_wall_area = 0.0
#     total_floor_area = 0.0
#     for surface in surfaces:
#         if surface.Surface_Type == 'Wall':
#             print(f"Wall: {surface.Name}, Area: {surface.Zone_Name}")

#     windows = self.idf.idfobjects['FENESTRATIONSURFACE:DETAILED']
#     for win in windows:
#         print(f"Window: {win.Name}, Parent Surface: {win.Building_Surface_Name}")



def get_new_idf_name(self):
    return self.idf_path + '_mod'