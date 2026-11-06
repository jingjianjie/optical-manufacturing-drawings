"""Pure drawing geometry. No ZOS, scipy, optimization or project imports."""
import numpy as np

def sphere_sag(c,r):
 q=1-(c*np.asarray(r))**2
 if np.any(q<0):raise ValueError("sphere radius smaller than profile extent")
 return c*np.asarray(r)**2/(1+np.sqrt(q))

def sag(m,f,r,outer):
 r=np.abs(np.asarray(r));j=f['surface'];rc=f['curve_end'];h=sphere_sag(m['c'][j],np.minimum(r,rc))
 if f['transition']>0:
  u=np.clip((r-rc)/f['transition'],0,1);h=h+u*(f['plateau']-float(sphere_sag(m['c'][j],rc)))
 else:h=np.where(r>rc,f['plateau'],h)
 if f['outer_bevel']>0:
  start=outer-f['outer_bevel'];f0=dict(f,outer_bevel=0.)
  atstart=sag(m,f0,start,outer)
  bevel=atstart+f['inward']*np.tan(np.deg2rad(f.get('bevel_angle',45.)))*(r-start)
  h=np.where(r>start,bevel,h)
 return h

def profiles(m,p):
 r=p['radius'];keys=[0,r]
 for f in [p['front_face'],p['back_face']]:keys += [f['curve_end'],f['curve_end']+f['transition'],r-f['outer_bevel']]
 rr=np.unique(np.r_[np.linspace(0,r,1601),np.clip(keys,0,r)]);y=np.r_[-rr[:0:-1],rr]
 z=np.r_[0,np.cumsum(m['t'][:-1])]
 x1=z[p['front']]+sag(m,p['front_face'],y,r);x2=z[p['back']]+sag(m,p['back_face'],y,r)
 return y,x1,x2
