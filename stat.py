import matplotlib.pyplot as plt
import numpy as np


def model_sats_chart():

    di = {
        #'llama-3.3':{
        #    'c2': 71.35,
        #    'c3': 91.6
        #},
        'gpt-4o': {
            'c2': 84.68,
            'c3': 79.37,
        },
        'gpt4.1-mini': {
            'c2': 87.05,
            'c3': 90.62
        },
        #'Deepseek-R1-llama': {
        #    'c2': 58.08,
        #    'c3': 85.25
        #},
        'gemini-2.0': {
            'c2': 82.03,
            'c3': 74.07,
        },
        'Mistral': {
            'c2': 86.67,
            'c3': 77.3
        },
        'Gemini-2.5-pro': {
            'c2': 90.81,
            'c3': 91.09
        },
        'Lint': {
            'c2': 63.8,
            'c3': 94.4
        },
        'PMD': {
            'c2': 68.4,
            'c3': 80.1
        },
        'aDoctor': {
            'c2': 24.3,
            'c3': 42.2
        },
        'DAAP': {
            'c2': 30.9,
            'c3': 87.5
        },
        'EcoAndroid': {
            'c2': 75,
            'c3': 0
        }
    }
    categories = list(di.keys())

    x = np.arange(len(categories))
    width = 0.25  # width of the bars

    fig, ax = plt.subplots(figsize=(8, 5))

    # Create bar pairs with different colors
    ax.bar(x - width/2, [di[cat]['c2'] for cat in categories], width, label='PfAnnlReal', color='#1f77b4')
    ax.bar(x + width / 2, [di[cat]['c3'] for cat in categories], width, label='PfAnnLLM', color='#ffbb78')
    #ax.bar(x - width/2, precision_a_max_c2, width, label='C2', color=['#1f77b4'])
    #ax.bar(x + width/2, precision_a_max_c3, width, label='C3', color=['#ffbb78'])
    ax.axhline(y=79.1, color='gray', linestyle='--', linewidth=1)
    # iterate the 5 rightmost bars to make them dashed
    for i, bar in enumerate(ax.patches[:5]):  # Only iterate over the first 10 bars
        bar.set_hatch('//')
    for i, bar in enumerate(ax.patches[-10:-5]):  # Only iterate over the first 10 bars
        bar.set_hatch('//')

    # Add labels and title
    ax.set_xlabel('Approaches')
    ax.set_ylabel('Precision (%)')
    ax.set_title('Precision of Different approaches')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=20, ha='right', fontsize=10)
    ax.legend()
    plt.tight_layout()
    plt.show()

def stats_issue_count():
    vibe_all_flagged_issues_projs = {
        "FlappyBird": 41,
        "GPTFlappyBird": 22,
        "Game2048": 34,
        "GPTGame2048": 27,
        "WeatherApp": 20,
        "GPTWeather": 6,
        "TodoNotes": 8,
        "GPTToDoNotes": 22,
        "ScientificCalculator": 13,
        "GPTScientificCalculator": 14,
        "GalleryApp": 25,
        "GPTPhotoGallery": 11,
    }

    vibe_tps_projs = {
        "FlappyBird": 8,
        "GPTFlappyBird": 8,
        "Game2048": 0,
        "GPTGame2048": 8,
        "WeatherApp": 7,
        "GPTWeather": 4,
        "TodoNotes": 5,
        "GPTToDoNotes": 11,
        "ScientificCalculator": 7,
        "GPTScientificCalculator": 5,
        "GalleryApp": 5,
        "GPTPhotoGallery": 8
    }

    similar_all_flagged_issues_projs = {
    "CalcYou" : 4,
    "Calculator-You": 1528,
    "game2048" : 0,
    "privacy-friendly-2048" : 398,
    "Gallery" : 0,
    "Tulsi": 396,
    "NotePad" : 476,
    "another-notes-app": 20,
    "World-Weather" : 443,
    "weather-overview" : 45,
    "beat-feet" : 0,
    "lato" : 151,
    }


    similar_tps_issues_projs = {
        "CalcYou": -1,
        "Calculator-You": -1,
        "game2048": -1,
        "privacy-friendly-2048": -1,
        "Gallery": -1,
        "Tulsi": -1,
        "NotePad": -1,
        "another-notes-app": -1,
        "World-Weather": -1,
        "weather-overview": -1,
        "beat-feet": -1,
        "lato": -1,
    }

    x = np.arange(len(vibe_tps_projs))
    width = 0.4  # width of the bars
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x, vibe_tps_projs.values(), width, color='#1f77b4')
    ax.set_xlabel('Tools')
    ax.set_ylabel('Number of Distinct Issues')
    ax.set_title('Number of Distinct Issues per Project')
    ax.set_xticks(x)
    ax.set_xticklabels(vibe_tps_projs.keys(), rotation=25, ha='right')
    plt.tight_layout()
    plt.show()


def main():
    model_sats_chart()
    #stats_issue_count()

if __name__ == '__main__':
    main()