import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider
import csv
from datetime import datetime

# Set up de conexion
ser = serial.Serial('COM3', 9600) 

# Datos
time_data = []
initial_temp_data = []
final_temp_data = []
flow_rate1_data = []
flow_rate2_data = []
pressure_data = []

# Contador
time_counter = 0
desired_temp = 25  # Temperatura desada

# Fecha y hora para csv
current_time = datetime.now().strftime('%Y-%m-%d_%H-%M')
csv_filename = f'{current_time}.csv'

# Enviar la temp deseada al arduino
def set_desired_temp(temp):
    ser.write(f"{temp}\n".encode('utf-8'))

# Lectura de datos de arduino
def read_data():
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        print("Raw Data:", line)  
        data = line.split(',')
        print("Parsed Data:", data)  

        if len(data) >= 5:
            try:
                initial_temp = float(data[0])
                final_temp = float(data[1])
                flow_rate1 = float(data[2])
                flow_rate2 = float(data[3])
                pressure_psi = float(data[4])

                return initial_temp, final_temp, flow_rate1, flow_rate2, pressure_psi
            except ValueError:
                print(f"Data conversion error: {line}")
                return None, None, None, None, None
        else:
            print(f"Unexpected data format: {line}")
            return None, None, None, None, None
    return None, None, None, None, None

# Filtros
def low_pass_filter(data, alpha=0.1):
    if len(data) < 2:
        return data[-1]
    return alpha * data[-1] + (1 - alpha) * data[-2]


def moving_average(data, window_size=5):
    if len(data) < window_size:
        return sum(data) / len(data)
    return sum(data[-window_size:]) / window_size

# Graficas
def update_plot(frame):
    global time_counter, desired_temp

    
    initial_temp, final_temp, flow_rate1, flow_rate2, pressure_psi = read_data()

    
    if initial_temp is not None and final_temp is not None:
        time_data.append(time_counter)
        initial_temp_data.append(initial_temp)
        final_temp_data.append(final_temp)

        
        flow_rate1 = low_pass_filter(flow_rate1_data + [flow_rate1])
        flow_rate2 = low_pass_filter(flow_rate2_data + [flow_rate2])
        pressure_psi = low_pass_filter(pressure_data + [pressure_psi])

        
        smoothed_flow_rate1 = moving_average(flow_rate1_data + [flow_rate1], window_size=5)
        smoothed_flow_rate2 = moving_average(flow_rate2_data + [flow_rate2], window_size=5)
        smoothed_pressure = moving_average(pressure_data + [pressure_psi], window_size=5)

        
        flow_rate1_data.append(smoothed_flow_rate1)
        flow_rate2_data.append(smoothed_flow_rate2)
        pressure_data.append(smoothed_pressure)

        print(f"Time: {time_counter}, Initial Temp: {initial_temp}, Final Temp: {final_temp}, Smoothed Flow Rate 1: {smoothed_flow_rate1}, Smoothed Flow Rate 2: {smoothed_flow_rate2}, Smoothed Pressure: {smoothed_pressure}")

        # Guardar en el CSV
        save_data_to_csv(time_counter, initial_temp, final_temp, smoothed_flow_rate1, smoothed_flow_rate2, smoothed_pressure)

    # configuracion graficas
    ax1.clear()
    ax2.clear()
    ax3.clear()

    ax1.plot(time_data, initial_temp_data, label='Initial Temperature (°C)')
    ax1.plot(time_data, final_temp_data, label='Final Temperature (°C)')
    ax1.axhline(y=desired_temp, color='r', linestyle=':', label='Desired Temperature (°C)')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Temperature (°C)')
    ax1.legend()
    ax1.set_title('Temperature vs Time')

    ax2.plot(time_data, flow_rate1_data, label='Flow Rate 1 (L/h)')
    ax2.plot(time_data, flow_rate2_data, label='Flow Rate 2 (L/h)')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Flow Rate (L/h)')
    ax2.legend()
    ax2.set_title('Flow Rates vs Time')

    ax3.plot(time_data, pressure_data, label='Pressure (PSI)')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Pressure (PSI)')
    ax3.legend()
    ax3.set_title('Pressure vs Time')

    
    time_counter += 1

# Csv
def save_data_to_csv(time, initial_temp, final_temp, flow_rate1, flow_rate2, pressure):
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([time, initial_temp, final_temp, flow_rate1, flow_rate2, pressure])

# Creacion de graficas
def main():
    global desired_temp, ax1, ax2, ax3

    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), constrained_layout=True)

    ani = animation.FuncAnimation(fig, update_plot, interval=1000, cache_frame_data=False)  # Update plot every 1 second

    # Seleccionador de temperatura deseada
    ax_temp = plt.axes([0.1, 0.1, 0.8, 0.03], facecolor='lightgoldenrodyellow')
    temp_slider = Slider(ax_temp, 'Desired Temp (°C)', 0.0, 100.0, valinit=desired_temp)


    def update_slider(val):
        global desired_temp
        desired_temp = temp_slider.val
        set_desired_temp(desired_temp)

    temp_slider.on_changed(update_slider)

    
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time (s)', 'Initial Temp (°C)', 'Final Temp (°C)', 'Flow Rate 1 (L/h)', 'Flow Rate 2 (L/h)', 'Pressure (PSI)'])

    plt.show()

if __name__ == "__main__":
    main()
