# %%
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.transforms as mtrans
import numpy as np


class Drawable:
    """
    Base Interface for objects that can be used by `Sketcher.Add`
    """

    def Draw(self, ax: plt.Axes, skparams: dict):
        """
        Base method called by `Sketcher.Draw`
        for all `Drawable` objects collection.
        Parameters
        ----------
        ax: `pyplot.Axes`
            Used to draw the on the Sketcher.
        skparams: `dict`
            Sketcher Global Other Parameters
        """
        pass

    def Size(self):
        """
        Base Method called by Sketcher to determine axes size
        Returns
        -------
        `tuple(tuple(float,float), tuple(float,float))`
            The rectangle ((x,y),(tox,toy)) that can encompass the object
        """
        pass

    def Pen(self):
        """
        Base Method called by Sketcher to determine the current pen position
        Returns
        -------
        tuple(float,float)
            The pen position (pX,pY)
        """
        pass


# %%
class Sketcher:
    """
    Create a new sketcher tool
    """

    def __init__(self, **kwargs):
        self.params = kwargs
        self.fig = plt.figure(figsize=self.params.get("figsize", (20, 20)))
        self.axes = self.fig.add_subplot()
        self.objs = []
        self.minx = np.inf
        self.maxx = -np.inf
        self.miny = np.inf
        self.maxy = -np.inf

    def Add(self, *drawables: Drawable):
        """
        Add new `Drawable` objects to this sketcher.
        Parameters
        ----------
        *objs: `Drawable`
            The objects to add
        """
        for obj in drawables:
            self.objs.append(obj)
            size = obj.Size()
            self.minx = min(self.minx, min(size[0][0], size[1][0]))
            self.miny = min(self.miny, min(size[0][1], size[1][1]))
            self.maxx = max(self.maxx, max(size[0][0], size[1][0]))
            self.maxy = max(self.maxy, max(size[0][1], size[1][1]))

    def Draw(self):
        """
        Plot all the sketcher objects
        """
        bw = 5
        msize = max(self.maxx - self.minx, self.maxy - self.miny) + bw
        self.axes.set_xlim(self.minx - bw, self.minx + msize)
        self.axes.set_ylim(self.miny - bw, self.miny + msize)
        if not self.params.get("showaxes", False):
            self.axes.set_axis_off()
        for o in self.objs:
            o.Draw(self.axes, self.params)
        plt.show()


# %%
class Line(Drawable):
    """
    Line Drawable for Sketcher
    Parameters
    ----------
    x,y: `float`
        begin point of the segment
    len,angle: `float`, optional
        length and angle in degrees of the segment
        required if toy,tox not provider
    tox,toy: `float`, optional
        end point of the segment
        required if lenght,angle not provided
    Other parameters
    ----------
    color: `str`
        set color
    transform: `Transform`
        transform object
    """

    def __init__(self, x, y, len=None, angle=None, tox=None, toy=None, **kwargs):
        if tox is None:
            tox = x + len * np.cos(np.deg2rad(angle))
        if toy is None:
            toy = y + len * np.sin(np.deg2rad(angle))
        self.x = x
        self.tox = tox
        self.y = y
        self.toy = toy
        self.params = kwargs

    def Size(self):
        if "transform" in self.params.keys():
            return tuple(
                self.params.get("transform").transform(
                    [(self.x, self.y), (self.tox, self.toy)]
                )
            )
        else:
            return ((self.x, self.y), (self.tox, self.toy))

    def Pen(self):
        if "transform" in self.params.keys():
            return tuple(self.params.get("transform").transform((self.tox, self.toy)))
        else:
            return (self.tox, self.toy)

    def Draw(self, ax: plt.Axes, skparams):
        pcolor = self.params.get("color", skparams.get("color", "black"))
        l = mlines.Line2D([self.x, self.tox], [self.y, self.toy], color=pcolor)
        if "transform" in self.params.keys():
            t = self.params.get("transform") + ax.transData
            l.set_transform(t)
        ax.add_line(l)


# %%
class Circle(Drawable):
    """
    Circle Drawable for Sketcher
    Parameters
    ----------
    x,y: `float`
        center point of the circle
    radius: `float`
        radius of the circle
    Other parameters
    ----------
    color: `str`
        set color
    transform: `Transform`
        transform object
    """

    def __init__(self, x, y, radius, **kwargs):
        self.params = kwargs
        self.radius = radius
        self.x = x
        self.y = y

    def Size(self):
        if "transform" in self.params.keys():
            return tuple(
                self.params.get("transform").transform(
                    [
                        (self.x - self.radius, self.y - self.radius),
                        (self.x + self.radius, self.y + self.radius),
                    ]
                )
            )
        else:
            return (
                (self.x - self.radius, self.y - self.radius),
                (self.x + self.radius, self.y + self.radius),
            )

    def Pen(self):
        if "transform" in self.params.keys():
            return tuple(
                self.params.get("transform").transform((self.x + self.radius, self.y))
            )
        else:
            return (self.x + self.radius, self.y)

    def Draw(self, ax: plt.Axes, skparams):
        pcolor = self.params.get("color", skparams.get("color", "black"))
        c = mpatches.Circle((self.x, self.y), self.radius, color=pcolor, fill=False)
        if "transform" in self.params.keys():
            t = self.params.get("transform") + ax.transData
            c.set_transform(t)
        ax.add_patch(c)


# %% [markdown]
# Unit Test
# %%
if "__main__" == __name__:
    tsk = Sketcher(showaxes=True, color="blue")
    pen = (0, 0)
    for i, alpha in enumerate(range(0, 360, 15), 1):
        # t = mtrans.Affine2D().skew(np.deg2rad(i+5),np.deg2rad(2*i+10))
        l1 = Line(pen[0], pen[1], 3, alpha, color="green")
        pen = l1.Pen()
        l2 = Line(pen[0], pen[1], 3, alpha - 5, color="red")
        pen = l2.Pen()
        c1 = Circle(pen[0] + 2, pen[1], 2)
        pen = c1.Pen()
        tsk.Add(l1, l2, c1)
    tsk.Draw()
# %%
