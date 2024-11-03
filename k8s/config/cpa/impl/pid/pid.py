import json
import time

class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint, previous_error = 0, integral = 0, max_integral = 10000, timestamp = time.time()):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.previous_error = previous_error
        self.integral = integral
        self.timestamp = timestamp
        self.max_integral = max_integral
    
    def update(self, current_value, timestamp):
        # Delta time
        delta_time = (timestamp - self.timestamp)

        # Calcula o erro
        error = self.setpoint - current_value
        
        # Calcula o termo proporcional
        P = self.Kp * error
        
        # Calcula o termo integral
        self.integral += error * delta_time

        # Limita o termo integral ao máximo permitido
        if self.integral > self.max_integral:
            self.integral = self.max_integral
        elif self.integral < -self.max_integral:
            self.integral = -self.max_integral

        I = self.Ki * self.integral
        
        # Calcula o termo derivativo
        D = self.Kd * (error - self.previous_error) / delta_time if delta_time > 0 else 0
        
        # Salva o erro atual para o próximo cálculo derivativo
        self.previous_error = error
        
        # Saída do controlador
        output = P + I + D

        # Atualiza timestamp com a ultima recebida
        self.timestamp = timestamp

        return output
    
    def to_dict(self):
        # Converte os atributos do controlador em um dicionário
        return {
            "Kp": self.Kp,
            "Ki": self.Ki,
            "Kd": self.Kd,
            "setpoint": self.setpoint,
            "previous_error": self.previous_error,
            "integral": self.integral,
            "max_integral": self.max_integral,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data):
        # Cria uma nova instância de PIDController a partir de um dicionário
        instance = cls(data["Kp"], data["Ki"], data["Kd"], data["setpoint"], data["previous_error"], data["integral"], data["max_integral"], data["timestamp"])
        return instance
    
    def serialize(self):
        return json.dumps(self, default=lambda o: o.to_dict())
    
def deserialize(json_data):
    data = json.loads(json_data)
    return PIDController.from_dict(data)