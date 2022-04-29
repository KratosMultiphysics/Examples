import KratosMultiphysics as KM
import KratosMultiphysics.ShallowWaterApplication as SW
from KratosMultiphysics.time_based_ascii_file_writer_utility import TimeBasedAsciiFileWriterUtility

def Factory(settings, model):
    if not isinstance(settings, KM.Parameters):
        raise Exception("expected input shall be a Parameters object, encapsulating a json string")
    return MassConservationOutputProcess(model, settings["Parameters"])

class MassConservationOutputProcess(KM.OutputProcess):
    '''Keep a tracking of the total mass during the computation.

    This process logs to file the total mass of water in a model_part
    during the specified interval in a computation.
    If relative_dry_height is set to -1 (default) all the domain will be
    considered. If it is greater or equal than 0, only the elements with
    wet fraction equal to 1 will be included.
    '''

    @staticmethod
    def GetDefaultParameters():
        return KM.Parameters("""{
            "model_part_name"      : "model_part",
            "interval"             : [0, "End"],
            "relative_dry_height"  : -1.0,
            "print_format"         : ".8f",
            "file_name"            : "",
            "output_path"          : ""
        }""")

    def __init__(self, model, settings):
        '''Constructor of MassConservationOutputProcess.'''
        KM.OutputProcess.__init__(self)
        settings.ValidateAndAssignDefaults(self.GetDefaultParameters())

        self.model_part_name = settings["model_part_name"].GetString()
        self.model_part = model.GetModelPart(self.model_part_name)
        self.interval = KM.IntervalUtility(settings)
        self.relative_dry_height = settings["relative_dry_height"].GetDouble()
        self.print_format = settings["print_format"].GetString()

        if (self.model_part.GetCommunicator().MyPID() == 0):
            output_file_settings = KM.Parameters()
            output_file_settings.AddValue("file_name", settings["file_name"])
            output_file_settings.AddValue("output_path", settings["output_path"])
            file_header = self._GetFileHeader()
            self.output_file = TimeBasedAsciiFileWriterUtility(
                self.model_part, output_file_settings, file_header).file

    @staticmethod
    def IsOutputStep():
        """See ExecuteFinalizeSolutionStep."""
        return False

    @staticmethod
    def PrintOutput():
        """See ExecuteFinalizeSolutionStep."""
        pass

    def ExecuteFinalizeSolutionStep(self):
        """Print the total mass into a log file.
        
        The PrintOutput is avoided for two reasons:
        - This process does not need processing variables at the ExecuteBeforeOutputStep.
        - Returning True at IsOutputStep will enforce the ExecuteBeforeOutputStep of the benchmark, which is very expensive.
        """
        current_time = self.model_part.ProcessInfo.GetValue(KM.TIME)

        if self.interval.IsInInterval(current_time):
            gravity = self.model_part.ProcessInfo.GetValue(KM.GRAVITY_Z)
            force = SW.ShallowWaterUtilities().ComputeHydrostaticForces(
                self.model_part.Elements, self.model_part.ProcessInfo, self.relative_dry_height)
            mass = -force[2] / gravity

            if self.model_part.GetCommunicator().MyPID() == 0:
                output_values = []
                output_values.append(str(current_time))
                output_values.append(format(mass, self.print_format))
                self.output_file.write(' '.join(output_values) + '\n')

    def _GetFileHeader(self):
        header = '# Total mass of water for model part ' + self.model_part_name + '\n'
        header += '#Time Mass\n'
        return header
