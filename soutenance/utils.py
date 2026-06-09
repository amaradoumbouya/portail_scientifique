def calculer_mention(note):

    if note < 10:
        return "Échec"

    elif note < 12:
        return "Passable"

    elif note < 14:
        return "Assez Bien"

    elif note < 16:
        return "Bien"

    elif note < 18:
        return "Très Bien"

    return "Excellent"