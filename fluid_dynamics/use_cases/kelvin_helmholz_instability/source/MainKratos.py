from KratosMultiphysics import *
from KratosMultiphysics.FluidDynamicsApplication import *
from fluid_dynamics_analysis import FluidDynamicsAnalysis
from fluid_solver_no_replace import FluidSolverNoReplace

class PeriodicFluidAnalysis(FluidDynamicsAnalysis):

    def __init__(self,model,parameters):
        super(PeriodicFluidAnalysis,self).__init__(model,parameters)

    def _CreateSolver(self):
        if self.project_parameters["problem_data"]["parallel_type"].GetString() == "OpenMP":
            return FluidSolverNoReplace(self.model,self.project_parameters["solver_settings"])
        else:
            from trilinos_fluid_solver_no_replace import TrilinosFluidSolverNoReplace
            return TrilinosFluidSolverNoReplace(self.model,self.project_parameters["solver_settings"])

    def ModifyInitialGeometry(self):
        print("Setting up periodic conditions")

        both_sides_periodic = False

        self._ApplyKelvinHelmholtzInitialCondition(both_sides_periodic)

        if not both_sides_periodic:
            self._ApplyNoSlip()


    def _ApplyKelvinHelmholtzInitialCondition(self, both_sides_periodic):
        from math import tanh,sin,exp,pi
        import random
        random.seed(20181024)

        y0 = 0.5  # vertical coordinate of the centerline
        L = 1.0   # height of the domain in real units
        N = 4     # desired number of vortices
        U = 1.0   # One half of the velocity difference (U1-U2 = 2U)
        di = L / (7.*N) # initial vorticitiy thickness

        #nu = U*di**3/1e4 # Target viscosity (Re = 1e4) Note: the paper uses a weird subgrid viscosity model with a viscosity in L^4/T units
        nu = U*di/1e4 # Target viscosity (Re = 1e4)
        #print(di/U) #this is the turnover time
        lambda_a = 7*di

        def _VelocityUnperturbed(node, yref):
            u = Array3()
            u[0] = U * tanh(2.*(node.Y - yref)/di)
            return u

        def _Noise(node, yref):
            noise_factor = 1e-3
            amplification = noise_factor*U*exp(-(node.Y-yref)**2/di**2)
            u = Array3()
            u[0] = amplification * sin(8*pi*node.X)
            u[1] = (random.random()-0.5)*amplification
            return u


        def _SingleLayerVelocity(node):
            # cancel noise on periodic sides to avoid introducing differences between them
            perturb = not (node.X in [0.0, 1.0] or node.Y in [0.0, 1.0])
            u = _VelocityUnperturbed(node,y0)
            if perturb:
                u = u + _Noise(node,y0)
            return u

        def _DoubleLayerVelocity(node):
            # cancel noise on periodic sides to avoid introducing differences between them
            perturb = not (node.X in [0.0, 1.0] or node.Y in [0.0, 1.0])

            if node.Y > 0.75:
                y_ref = 1.0
                factor = -1.0
            elif node.Y > 0.25:
                y_ref = 0.5
                factor = 1.0
            else:
                y_ref = 0.0
                factor = -1.0

            u = _VelocityUnperturbed(node,y_ref)
            if perturb:
                u = u + _Noise(node,y_ref)
            return u * factor

        if both_sides_periodic:
            VelocityFunction = _DoubleLayerVelocity
        else:
            VelocityFunction = _SingleLayerVelocity

        model_part = self.model.GetModelPart(self.project_parameters["solver_settings"]["model_part_name"].GetString())

        rho = model_part.GetProperties()[1].GetValue(DENSITY)
        model_part.GetProperties()[1].SetValue(DYNAMIC_VISCOSITY,rho*nu)

        for node in model_part.Nodes:
            node.SetSolutionStepValue(VELOCITY,0,VelocityFunction(node))
            node.SetSolutionStepValue(VISCOSITY,0,nu)


    def _ApplyNoSlip(self):
        top_side    = self.model.GetModelPart("NoSlip2D_top")
        for node in top_side.Nodes:
            node.Fix(VELOCITY_X)
            node.Fix(VELOCITY_Y)

        bottom_side = self.model.GetModelPart("NoSlip2D_bottom")
        for node in bottom_side.Nodes:
            node.Fix(VELOCITY_X)
            node.Fix(VELOCITY_Y)


if __name__ == "__main__":
    from sys import argv

    if len(argv) > 2:
        err_msg =  'Too many input arguments!\n'
        err_msg += 'Use this script in the following way:\n'
        err_msg += '- With default parameter file (assumed to be called "ProjectParameters.json"):\n'
        err_msg += '    "python periodic_fluid_analysis.py"\n'
        err_msg += '- With custom parameter file:\n'
        err_msg += '    "python periodic_fluid_analysis.py <my-parameter-file>.json"\n'
        raise Exception(err_msg)

    if len(argv) == 2: # ProjectParameters is being passed from outside
        parameter_file_name = argv[1]
    else: # using default name
        parameter_file_name = "ProjectParameters.json"

    with open(parameter_file_name,'r') as parameter_file:
        parameters = Parameters(parameter_file.read())

    model = Model()
    simulation = PeriodicFluidAnalysis(model,parameters)
    simulation.Run()

