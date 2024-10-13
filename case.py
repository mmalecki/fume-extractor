import math
import cq_queryabolt as queryabolt
import cadquery as cq

class Workplane(queryabolt.WorkplaneMixin, cq.Workplane):
    pass

pressFit = 0.05
fit = 0.1
looseFit = 0.5

# Chamfer
c = 1
f = 5

fanBolt = "M2.5"

magnetD = 5
magnetH = 5
magnetS = 20

wallT = 1.6
baseT = magnetH + wallT

fanNutH = queryabolt.nutData(fanBolt)["thickness"]
fanNutW = queryabolt.nutData(fanBolt)["width"]
fanNutWallH = fanNutH + wallT
fanNutWallD = fanNutW + 2*wallT
fanMountT = 1.5 * fanNutWallH
fanBoltHeadT = queryabolt.boltData(fanBolt, kind="socket_head")["head_length"]

fanW = 30
fanH = 30
fanT = 10
fanTFit = fanT + fit + fanBoltHeadT
fanMountW = 24
fanCount = 2

w = fanCount * (fanW + fit) + 2 * wallT
l = fanTFit + fanMountT

def fanMount():
    plate = Workplane("XY").rect(w, l).extrude(baseT)

    plate.faces(">Z").workplane().tag("top")
    plate.faces("<Z").workplane().tag("bottom")

    plate = plate.faces(">Y").workplane(centerOption="CenterOfBoundBox").rarray(magnetS, 1, math.floor(w / magnetS), 1).hole(magnetD, magnetH)

    plate = plate.workplaneFromTagged("top").move(0, -l / 2 + fanMountT / 2).rect(w, fanMountT).extrude(fanNutWallD)
    plate.faces("<Y").workplane().tag("fanNuts").end()

    def fanOffset(f):
        return -w / 2 + (fanW - fanMountW) / 2 + f * (fanW + fit) + wallT

    plate = plate.faces(">Y").workplane().center(0,fanNutWallD / 2)
    for fan in range(0, fanCount):
        plate = plate.pushPoints([(fanOffset(fan), 0), (fanOffset(fan) + fanMountW, 0)]).boltHole(fanBolt)

    plate = plate.workplaneFromTagged("fanNuts").center(0, fanNutWallD / 2)
    for fan in range(0, fanCount):
        plate = plate.pushPoints([(fanOffset(fan), 0), (fanOffset(fan) + fanMountW, 0)]).nutcatchParallel(fanBolt)

    # Fan airflow cutouts
    plate = plate.faces(">Z").workplane(centerOption="CenterOfBoundBox").tag("fanMount")
    for fan in range(0, fanCount):
        plate = plate.workplaneFromTagged("fanMount").move(fanOffset(fan) + fanMountW / 2, 0).rect(fanMountW - fanNutW - 2 * wallT, fanMountT).extrude(-fanNutWallD / 2, combine='cut')

    # Bottom magnet holes
    plate = plate.workplaneFromTagged("bottom").center(0, l / 2 - magnetD / 2 - wallT).rarray(magnetS, 1, math.floor(w / magnetS), 1).hole(magnetD, magnetH)

    # Chamfers
    # In my case, these are art rather than exact science.
    # If you changed the parameters and the model fails
    # to render with a "BRep_API: command not done",
    # removing these is a good place to start debugging.
    plate = (plate.faces("<Z[1]").edges("|Y").fillet(c * 2))
    plate = (plate.faces(">Z").edges("|Y").fillet(c * 2))
    plate = plate.edges("(>>X or <<X) and (>Z or <Z[1] or <Z[2])").chamfer(c)
    plate = plate.faces("<Z").chamfer(c / 2)
    plate = plate.edges("<Y and |Z and (>>X or <<X)").chamfer(c / 2)
    plate = (plate.faces(">Z[2]").edges("|Y or |X").chamfer(c / 2))
    return plate

def basketBottom():
    slot = 3.5 # reuse nevermore carbon
    slotHS = 1.25 * slot
    slotVS = 0.75 * slot

    h = baseT + fanH + wallT
    basketW = w + 2 * wallT
    basketL = fanT + 2 * wallT

    basket = Workplane("XY").rect(basketW, basketL).extrude(h).faces("+Z").workplane().rect(w, basketL - 2 * wallT).cutBlind(-fanH)
    basket.faces("<Z").workplane(centerOption="CenterOfBoundBox").tag("bottom").end()
    basket.faces("<Y").workplane(centerOption="CenterOfBoundBox").tag("fanMate").end()

    # Fan magnet holes
    basket = basket.workplaneFromTagged("fanMate").center(0, -fanH / 2).rarray(magnetS, 1, math.floor(w / magnetS), 1).hole(magnetD, magnetH)

    # Fan airflow cover
    coverT = wallT - fit
    basket = basket.workplaneFromTagged("fanMate").center(0, h / 2 - fanH / 2 - wallT).rarray(basketW  - coverT, 1, 2, 1).rect(wallT - fit, fanH).extrude(fanTFit)
    basket = basket.workplaneFromTagged("fanMate").center(0, h / 2 - wallT / 2).rect(basketW, wallT).extrude(fanTFit)

    # Bottom magnet holes
    # basket = basket.workplaneFromTagged("bottom").rarray(magnetS, 1, math.floor(w / magnetS), 1).hole(magnetD + pressFit, magnetH + fit)

    # Ventilation slots
    basket = basket.faces(">Y").workplane(centerOption="CenterOfBoundBox").center(0, baseT / 2).rarray(slotHS, slotVS, math.floor(w / slotHS) - 1 , math.floor(fanH / slotVS) - 1).slot2D(slot, slot/2).cutThruAll()

    # Chamfer the ventilation slots
    basket = basket.faces(">Y").edges("%Circle").chamfer(slot / 10)
    basket = basket.faces("<Y[1]").edges("%Circle").chamfer(slot / 10)
    basket = basket.faces(">Y[1]").edges("%Circle").chamfer(slot / 10)
    basket = basket.faces(">Y[2]").edges("%Circle").chamfer(slot / 10)

    basket = basket.faces("<Z").chamfer(c / 2)
    basket = basket.faces(">Z").chamfer(c / 2)
    basket = (basket.faces(">Z[1]").edges("<Y").chamfer(fanTFit / 2))
    basket = basket.faces("<Y").edges().chamfer(wallT / 6)
    basket = basket.faces(">Y").edges(">>X or <<X or >>Z or <<Z").chamfer(c / 2)

    return basket

show_object(fanMount(), name="fanMount")
# show_object(basketBottom().val().translate((0, l * 1.5, 0)), name="basketBottom")
