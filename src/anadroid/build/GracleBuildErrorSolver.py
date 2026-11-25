"""Deprecated name of anadroid.build.GradleBuildErrorSolver. This module will be removed in a next release."""
import warnings

from anadroid.build.GradleBuildErrorSolver import *  # noqa: F401,F403

warnings.warn("anadroid.build.GracleBuildErrorSolver is deprecated. Use anadroid.build.GradleBuildErrorSolver",
              DeprecationWarning, stacklevel=2)
