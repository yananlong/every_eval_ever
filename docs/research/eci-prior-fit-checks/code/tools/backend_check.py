import pytensor, pytensor.tensor as pt
x = pt.dvector("x"); f = pytensor.function([x], (x**2).sum())
print("mode:", type(f.maker.mode).__name__, getattr(f.maker.mode, "name", None), "linker:", type(f.maker.linker).__name__)
print("config.linker:", pytensor.config.linker, "config.mode:", pytensor.config.mode)
