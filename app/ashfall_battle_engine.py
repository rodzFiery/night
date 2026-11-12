"""ASHFALL 7.6 — deterministic battle resolution, shared by preview and combat.

All values are server-calculated. No randomness, paid modifiers or client power.
"""
STATS={"infantry":{"power":4,"guard":5},"rider":{"power":6,"guard":3},"hunter":{"power":7,"guard":2}}

def resolve(quantity,unit,opponent,bonus=0,attributes=None):
 if unit not in STATS or not isinstance(quantity,int) or not 1<=quantity<=1000:
  raise ValueError("Invalid unit or troop count")
 if opponent<0:raise ValueError("Invalid opponent strength")
 a=attributes or {}
 attack=max(0,float(a.get("attack",0)))
 defense=max(0,float(a.get("defense",0)))
 health=max(0,float(a.get("health",0)))
 capacity=max(0,int(a.get("march_capacity",0)))
 # Hero command increases marching capacity beyond the base 1000-troop interface
 # but never reduces the player's available troop pool.
 effective_capacity=min(1000,250+capacity) if capacity else 1000
 if quantity>effective_capacity:raise ValueError("Troop deployment exceeds command capacity")
 power=int(quantity*STATS[unit]["power"]*(1+max(0,float(bonus)))*(1+attack/100))
 victory=power>=opponent
 base_loss=min(quantity,max(1,(opponent*2)//(STATS[unit]["guard"]*10))) if victory else min(quantity,max(1,quantity//3))
 # Defense and hero vitality mitigate abstract attrition, never below one.
 mitigation=1+defense/100+min(0.5,health/10000)
 loss=max(1,int(base_loss/mitigation))
 return {"player_power":power,"opponent_power":opponent,"victory":victory,
         "deployed":quantity,"returned":quantity-loss,"losses":loss,
         "capacity":effective_capacity,
         "modifiers":{"attack":attack,"defense":defense,"health":health,"hero_bonus":round(float(bonus)*100,3)}}
