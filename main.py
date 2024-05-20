import telebot
import googlemaps
from config import TOKEN, GOOGLE_API_KEY
from datetime import datetime

bot = telebot.TeleBot(TOKEN)
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
user_data = {}


@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(message.chat.id, "Я пошель какать...")


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
        bot.send_message(message.chat.id,
                         "Invalid input. Please enter the dimensions in the format length x width x height:")
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
    estimate_cost_final(chat_id)


def calculate_distance(origin, destination):
    now = datetime.now()
    distance_matrix = gmaps.distance_matrix(origins=origin, destinations=destination, mode="driving",
                                            departure_time=now)

    try:
        distance = distance_matrix['rows'][0]['elements'][0]['distance']['text']
        duration = distance_matrix['rows'][0]['elements'][0]['duration']['text']
        return distance, duration
    except Exception as e:
        return None, None


def estimate_cost_final(chat_id):
    weight = user_data[chat_id]['weight']
    dimensions = user_data[chat_id]['dimensions']
    origin = user_data[chat_id]['origin']
    destination = user_data[chat_id]['destination']

    distance, duration = calculate_distance(origin, destination)

    if distance and duration:
        base_cost = 5.0
        if weight > 30:
            weight_cost = weight * 2.0  # cost per kg
        else:
            weight_cost = 3
        volume_cost = (dimensions[0] * dimensions[1] * dimensions[2]) / 5000.0
        distance_cost = 1

        distance_value = float(distance.split()[0].replace(',', ''))
        total_cost = base_cost + weight_cost + volume_cost + (distance_value * distance_cost)

        bot.send_message(chat_id,
                         f"The estimated cost for shipping from {origin} to {destination} is ${total_cost:.2f}.")
        bot.send_message(chat_id, f"The distance is {distance} and it takes approximately {duration}.")
    else:
        bot.send_message(chat_id,
                         "Unable to calculate the distance. Please check the origin and destination addresses.")

# Start polling
if __name__ == '__main__':
    bot.polling(none_stop=True)
