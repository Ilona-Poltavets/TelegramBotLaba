# main.py
import telebot
import googlemaps
from config import TOKEN, GOOGLE_API_KEY
from datetime import datetime
from db_connection import init_db, save_order, get_orders

bot = telebot.TeleBot(TOKEN)
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
user_data = {}

# Initialize the database
init_db()

delivery_types = {
    'Express': {'name': 'Express', 'cost_per_km': 3.0, 'duration_multiplier': 1.0},
    'Standard': {'name': 'Standard', 'cost_per_km': 2.0, 'duration_multiplier': 1.3},
    'Economy': {'name': 'Economy', 'cost_per_km': 0.5, 'duration_multiplier': 1.5}
}


@bot.message_handler(commands=["start"])
def start_message(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Welcome! Use /order_delivery to start ordering your delivery.")


@bot.message_handler(commands=["order_delivery"])
def order_delivery(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    bot.send_message(chat_id, "Let's order your delivery. Please enter the weight of the shipment (in kg):")
    bot.register_next_step_handler(message, get_order_weight)


def get_order_weight(message):
    try:
        chat_id = message.chat.id
        weight = float(message.text)
        user_data[chat_id]['weight'] = weight
        bot.send_message(chat_id, "Please enter the dimensions of the shipment (length x width x height in cm):")
        bot.register_next_step_handler(message, get_order_dimensions)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input. Please enter a numerical value for the weight:")
        bot.register_next_step_handler(message, get_order_weight)


def get_order_dimensions(message):
    try:
        chat_id = message.chat.id
        dimensions = message.text.split('x')
        if len(dimensions) != 3:
            raise ValueError("Incorrect dimensions format")
        length, width, height = map(float, dimensions)
        user_data[chat_id]['dimensions'] = (length, width, height)
        bot.send_message(chat_id, "Please enter the origin of the shipment:")
        bot.register_next_step_handler(message, get_order_origin)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input. Please enter the dimensions in the format length x width x height:")
        bot.register_next_step_handler(message, get_order_dimensions)


def get_order_origin(message):
    chat_id = message.chat.id
    origin = message.text
    user_data[chat_id]['origin'] = origin
    bot.send_message(chat_id, "Please enter the destination of the shipment:")
    bot.register_next_step_handler(message, get_order_destination)


def get_order_destination(message):
    chat_id = message.chat.id
    destination = message.text
    user_data[chat_id]['destination'] = destination

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Express')
    markup.add('Standard')
    markup.add('Economy')
    bot.send_message(chat_id, "Please select the type of delivery:", reply_markup=markup)
    bot.register_next_step_handler(message, get_order_delivery_type)


def get_order_delivery_type(message):
    chat_id = message.chat.id

    bot.send_message(chat_id, "Please select the type of delivery:\n1. Express ($3 per km)\n2. Standard ($2 per km)\n3. Economy ($0.5 per km)")
    
    delivery_choice = message.text.strip()
    if delivery_choice in delivery_types:
        user_data[chat_id]['delivery_type'] = delivery_types[delivery_choice]
        calculate_order_cost(chat_id)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Express')
        markup.add('Standard')
        markup.add('Economy')
        bot.send_message(chat_id, "Invalid choice. Please select the type of delivery:", reply_markup=markup)
        bot.register_next_step_handler(message, get_order_delivery_type)


def calculate_distance(origin, destination):
    now = datetime.now()
    distance_matrix = gmaps.distance_matrix(origins=origin, destinations=destination, mode="driving", departure_time=now)
    try:
        distance = distance_matrix['rows'][0]['elements'][0]['distance']['text']
        duration = distance_matrix['rows'][0]['elements'][0]['duration']['text']
        return distance, duration
    except Exception as e:
        return None, None


def calculate_order_cost(chat_id):
    weight = user_data[chat_id]['weight']
    dimensions = user_data[chat_id]['dimensions']
    origin = user_data[chat_id]['origin']
    destination = user_data[chat_id]['destination']
    delivery_type = user_data[chat_id]['delivery_type']

    distance, duration = calculate_distance(origin, destination)
    duration=duration*delivery_type['duration_multiplier']

    if distance and duration:
        base_cost = 5.0
        # weight_cost = weight if weight > 30 else 3.0
        # volume_cost = (dimensions[0] * dimensions[1] * dimensions[2]) / 5000.0
        distance_value = float(distance.split()[0].replace(',', ''))
        distance_cost = distance_value * delivery_type['cost_per_km']

        total_cost = base_cost + distance_cost

        user_data[chat_id]['distance'] = distance
        user_data[chat_id]['duration'] = duration
        user_data[chat_id]['cost'] = total_cost

        save_order(chat_id, user_data[chat_id])

        bot.send_message(chat_id, f"The estimated cost for shipping from {origin} to {destination} using {delivery_type['name']} delivery is ${total_cost:.2f}.")
        bot.send_message(chat_id, f"The distance is {distance} and it takes approximately {duration}.")
    else:
        bot.send_message(chat_id, "Unable to calculate the distance. Please check the origin and destination addresses.")


@bot.message_handler(commands=["estimate_cost"])
def estimate_cost(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    bot.send_message(chat_id, "Let's estimate the shipping cost. Please enter the weight of the shipment (in kg):")
    bot.register_next_step_handler(message, get_weight)


def get_weight(message):
    try:
        chat_id = message.chat.id
        weight = float(message.text)
        user_data[chat_id]['weight'] = weight
        bot.send_message(chat_id, "Please enter the dimensions of the shipment (length x width x height in cm):")
        bot.register_next_step_handler(message, get_dimensions)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input. Please enter a numerical value for the weight:")
        bot.register_next_step_handler(message, get_weight)


def get_dimensions(message):
    try:
        chat_id = message.chat.id
        dimensions = message.text.split('x')
        if len(dimensions) != 3:
            raise ValueError("Incorrect dimensions format")
        length, width, height = map(float, dimensions)
        user_data[chat_id]['dimensions'] = (length, width, height)
        bot.send_message(chat_id, "Please enter the origin of the shipment:")
        bot.register_next_step_handler(message, get_origin)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input. Please enter the dimensions in the format length x width x height:")
        bot.register_next_step_handler(message, get_dimensions)


def get_origin(message):
    chat_id = message.chat.id
    origin = message.text
    user_data[chat_id]['origin'] = origin
    bot.send_message(chat_id, "Please enter the destination of the shipment:")
    bot.register_next_step_handler(message, get_destination)


def get_destination(message):
    chat_id = message.chat.id
    destination = message.text
    user_data[chat_id]['destination'] = destination
    bot.send_message(chat_id, "Please select the type of delivery:\n1. Express ($3 per km)\n2. Standard ($2 per km)\n3. Economy ($0.5 per km)")
    get_delivery_type(message)


def get_delivery_type(message):
    chat_id = message.chat.id

    delivery_choice = message.text.strip()
    if delivery_choice in delivery_types:
        user_data[chat_id]['delivery_type'] = delivery_types[delivery_choice]
        estimate_cost_final(chat_id)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Express')
        markup.add('Standard')
        markup.add('Economy')
        bot.send_message(chat_id, "Invalid choice. Please select the type of delivery:", reply_markup=markup)
        bot.register_next_step_handler(message, get_delivery_type)


def estimate_cost_final(chat_id):
    weight = user_data[chat_id]['weight']
    dimensions = user_data[chat_id]['dimensions']
    origin = user_data[chat_id]['origin']
    destination = user_data[chat_id]['destination']
    delivery_type = user_data[chat_id]['delivery_type']

    distance, duration = calculate_distance(origin, destination)
    duration = duration * delivery_type['duration_multiplier']

    if distance and duration:
        base_cost = 5.0
        # weight_cost = weight * 2.0
        # volume_cost = (dimensions[0] * dimensions[1] * dimensions[2]) / 5000.0
        distance_value = float(distance.split()[0].replace(',', ''))
        distance_cost = delivery_type['cost_per_km']

        distance_value = float(distance.split()[0].replace(',', ''))
        total_cost = base_cost + (distance_value * distance_cost)

        bot.send_message(chat_id, f"The estimated cost for shipping from {origin} to {destination} is ${total_cost:.2f}.")
        bot.send_message(chat_id, f"The distance is {distance} and it takes approximately {duration}.")
    else:
        bot.send_message(chat_id, "Unable to calculate the distance. Please check the origin and destination addresses.")


@bot.message_handler(commands=["find_transport"])
def find_transport(message):
    bot.send_message(message.chat.id, "You can schedule pickup of your cargo at a specific time and place by contacting our support team.")


@bot.message_handler(commands=["track_shipment"])
def track_shipment(message):
    bot.send_message(message.chat.id, "You can track your transport by using the tracking number provided by the carrier.")


@bot.message_handler(commands=["request_offer"])
def request_offer(message):
    bot.send_message(message.chat.id, "You can request a commercial offer for the transportation of cargo by contacting our support team.")


@bot.message_handler(commands=["schedule_pickup"])
def schedule_pickup(message):
    chat_id = message.chat.id
    orders = get_orders(chat_id)
    if orders:
        for order in orders:
            weight, length, width, height, origin, destination, distance, duration, cost = order
            bot.send_message(chat_id,
                             f"Order:\nWeight: {weight} kg\nDimensions: {length}x{width}x{height} cm\n"
                             f"From: {origin}\nTo: {destination}\nDistance: {distance}\nDuration: {duration}\nCost: ${cost:.2f}")
    else:
        bot.send_message(chat_id, "No orders found. Please use /order_delivery to create an order.")


@bot.message_handler(commands=["calculate_volume"])
def calculate_volume(message):
    bot.send_message(message.chat.id, "You can calculate the cargo volume by measuring its length, width, and height, and then multiplying these dimensions together.")


@bot.message_handler(commands=["report_delay"])
def report_delay(message):
    bot.send_message(message.chat.id, "If there is a delay in the delivery of your cargo, please contact our support team to report it.")


@bot.message_handler(commands=["stop"])
def stop_command(message):
    chat_id = message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]
    bot.send_message(chat_id, "The order process has been stopped. Use /order_delivery to start again.")


# Start polling
if __name__ == '__main__':
    bot.polling(none_stop=True)
