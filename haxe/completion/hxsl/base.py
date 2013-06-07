
def auto_complete( project, view , offset, prefix ) :
    comps = []
    for t in ["Float","Float2","Float3","Float4","Matrix","M44","M33","M34","M43","Texture","CubeTexture","Int","Color","include"] :
        comps.append( ( t , "hxsl Type" ) )
    return comps