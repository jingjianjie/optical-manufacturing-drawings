"""Shared per-page manufacturing policy; user conventions, not universal GB rules."""
TYPES = {'cemented','coated','uncoated'}
LABELS = {'cemented':'胶合面','coated':'镀膜面','uncoated':'不镀膜面'}

def check_geometry(parts):
    for p in parts:
        for side in ('front_face','back_face'):
            if p[side]['outer_bevel'] <= 0:
                raise ValueError(f'Every face needs an edge chamfer: {p["name"]}/{side}')

def classify(parts, selected, face_types):
    check_geometry(selected)
    shared={p['back']+1 for p in parts for q in parts if p is not q and p['back']==q['front']}
    numbers=[selected[0]['front']+1, selected[-1]['back']+1]
    if len(selected)>1:numbers.insert(1,selected[0]['back']+1)
    result=[]
    for i,n in enumerate(numbers,1):
        role=face_types.get(str(n))
        if role not in TYPES:raise ValueError(f'Missing/invalid explicit face type at ZOS{n}')
        if (n in shared)!=(role=='cemented'):raise ValueError(f'Cement relationship conflict ZOS{n}')
        result.append({'local':f'S{i}','zos':n,'role':role,'label':LABELS[role]})
    kind='胶合件' if len(selected)>1 else ('单片:子片' if any(x['role']=='cemented' for x in result) else '单片')
    return kind,result
