import base64
import webbrowser
from flask import Blueprint ,flash, jsonify, render_template, request, redirect, send_file, send_from_directory, url_for
from flask_login import login_required, current_user
from .models import ChatMessage, db


import natsort
import os
import shutil

from .db_utility import commit_current_user_details, get_current_path_details, get_current_course_details, commit_current_course_details, \
    commit_current_path_details, get_current_user_details
from .os_utility import check_code_present, create_dir, delete_dir, load_topics, load_toc_if_exist, build_toc_render_items, \
    load_folder, build_folder_structure_for_monaco_sidebar

main = Blueprint('main', __name__)
root_course_dir = os.getenv('course_dir', '.')
OS_ROOT = os.path.join(os.path.expanduser('~'), 'EducativeViewer')


@main.route('/')
def index():
    return render_template('index.html')


'''
Endpoint to load the course list directory
'''
@main.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    highlight_idx = None
    last_visited_topic = ""
    last_visited_index = 0
    course_dir = root_course_dir
    temp_folder_path = os.path.join(OS_ROOT, "temp", current_user.username)
    delete_dir(temp_folder_path)

    '''
    Change the download button color based on the download access
    '''
    download_button_color = '#ed4444 !important'
    current_user_details = get_current_user_details(current_user.username)
    if current_user_details.downloadaccess:
        download_button_color = '#82f382 !important'


    current_path_details = get_current_path_details(current_user.username)
    if current_path_details is not None:
        course_dir = current_path_details.last_visited_directory
        last_visited_course = current_path_details.last_visited_course
        current_course_details = get_current_course_details(current_user.username, last_visited_course)
        if current_course_details is not None:
            last_visited_topic = current_course_details.last_visited_topic
            last_visited_index = current_course_details.last_visited_index

    if request.method == "POST":
        if request.form.get("folder"):
            '''
            Traversing in folders
            '''
            folder = request.form.get("folder")
            course_dir = os.path.join(course_dir, folder)
            folders = natsort.natsorted(os.listdir(course_dir))
            last_visited_course = course_dir.split(os.path.sep)[-1]
            current_course_details = get_current_course_details(current_user.username, last_visited_course)
            if current_course_details is not None:
                last_visited_topic = current_course_details.last_visited_topic
                last_visited_index = current_course_details.last_visited_index
            if folder + ".html" in folders:
                '''
                If topic.html is found, render the html then
                '''
                commit_current_course_details(username=current_user.username,
                                              last_visited_course=course_dir.split(os.path.sep)[-2],
                                              last_visited_topic=last_visited_topic,
                                              last_visited_index=last_visited_index)
                return redirect(url_for('main.courses') + f"/{folder}")
            if folder + ".html" not in folders:
                '''
                It is a folder, traverse inside it.
                '''
                commit_current_path_details(username=current_user.username,
                                            last_visited_directory=course_dir,
                                            last_visited_course=last_visited_course)
                '''
                If the last visited topic is present in the folder, highlight the folder.
                '''
                if last_visited_topic in folders:
                    highlight_idx = folders.index(last_visited_topic)

                '''
                If table of contents.json is present, render the html using toc
                '''
                toc = load_toc_if_exist(course_dir)
                if toc:
                    toc_items = build_toc_render_items(toc, highlight_idx)
                    return render_template("courses_toc.html", toc_items=toc_items, folder=folder, download_button_color=download_button_color)
                return render_template("courses.html", folder_list=folders, folder=folder, highlight_idx=highlight_idx, download_button_color=download_button_color)
        '''
        If above condition doesnt satisfy then Traversing out folders  but not exit the root_course_dir
        '''
        if len(root_course_dir) < len(course_dir):
            course_dir = os.path.sep.join(course_dir.split(os.path.sep)[:-1])
            folders = natsort.natsorted(load_folder(course_dir))
            last_visited_course = course_dir.split(os.path.sep)[-1]
            commit_current_path_details(username=current_user.username, last_visited_directory=course_dir,
                                        last_visited_course=last_visited_course)

            if last_visited_topic in folders:
                highlight_idx = folders.index(last_visited_topic)
            return render_template("courses.html", folder_list=folders, folder=last_visited_course,
                                   highlight_idx=highlight_idx, download_button_color=download_button_color)
    '''
    If above condition doesnt satisfy then it is a GET request
    '''
    folders = natsort.natsorted(load_folder(course_dir))
    folder = os.path.split(course_dir)[-1]
    if last_visited_topic in folders:
        highlight_idx = folders.index(last_visited_topic)
    toc = load_toc_if_exist(course_dir)
    if toc:
        toc_items = build_toc_render_items(toc, highlight_idx)
        return render_template("courses_toc.html", toc_items=toc_items, folder=folder, download_button_color=download_button_color)
    return render_template("courses.html", folder_list=folders, folder=folder, highlight_idx=highlight_idx, download_button_color=download_button_color)


'''
Endpoint to load topics.
'''
@main.route("/courses/<topics>", methods=['GET', 'POST'])
@login_required
def topics(topics):
    current_path_details = get_current_path_details(current_user.username)
    if current_path_details is None:
        flash("No path details found. Redirecting to courses.")
        return redirect(url_for('main.courses'))
    course_dir = current_path_details.last_visited_directory
    last_visited_course = current_path_details.last_visited_course
    # current_course_details = get_current_course_details(current_user.username, last_visited_course)
    # topic_index = current_course_details.last_visited_index
    folders = natsort.natsorted(load_folder(course_dir))
    print(topics , "-------------- topics")
    if topics in folders:
        topic_index = int(topics.split("-")[0])
        commit_current_course_details(
            username=current_user.username,
            last_visited_course=last_visited_course,
            last_visited_topic=topics,
            last_visited_index=topic_index
        )
    itr = topic_index 
    toc = load_toc_if_exist(course_dir)
    if toc:
        return topics_toc(topics, course_dir, toc, itr)
    topic_folders = natsort.natsorted(load_topics(course_dir))
    try:
        itr = int(topic_folders.index(topics))
    except ValueError:
        pass
    if request.method == "POST":
        if "back" in request.form and itr > 0:
            itr -= 1
        elif "next" in request.form and itr < len(topic_folders) - 1:
            itr += 1
        elif "sidebar-topic" in request.form:
            itr = int(request.form.get('sidebar-topic'))
        elif "home" in request.form:
            return redirect(url_for('main.courses'))
        elif request.form.get("code_filesystem"):
            path = f"file:///{course_dir}/{topic_folders[itr]}".replace("\\", "/")
            webbrowser.open(path)
    '''
    GET request, this is used to refresh the webpage if required    
    '''
    commit_current_course_details(username=current_user.username,
                                  last_visited_course=last_visited_course,
                                  last_visited_topic=topic_folders[itr],
                                  last_visited_index=itr)

    template_folder = "/".join(course_dir[len(root_course_dir) + 1:].split(os.path.sep))
    webpage = f"{template_folder}/{topic_folders[itr]}/{topic_folders[itr]}.html"
    is_code_present = check_code_present(course_dir, topic_folders[itr])
    rendered_html = render_template(
        "topics.html", code_present=is_code_present, webpage=webpage, folder=f"{topic_folders[itr]}",
        folder_list=topic_folders, itr=itr)
    return rendered_html

# Topics Toc
def topics_toc(topics, course_dir, toc, itr):
    toc_items = build_toc_render_items(toc)
    try:
        itr = next(i for i, toc_item in enumerate(toc_items) if toc_item['title'] == topics)
    except StopIteration:
        pass

    # Determine previous and next topics
    prev_topic = toc_items[itr - 1]['title'] if itr > 0 else None
    next_topic = toc_items[itr + 1]['title'] if itr < len(toc_items) - 1 else None

    if request.method == "POST":
        if "back" in request.form and itr > 0:
            if toc_items[itr - 1]['is_category']:
                if itr - 1 != 0:
                    itr -= 1
                else:
                    itr += 1
            itr -= 1
        elif "next" in request.form and itr < len(toc_items) - 1:
            if toc_items[itr + 1]['is_category']:
                if itr + 1 != len(toc_items) - 1:
                    itr += 1
                else:
                    itr -= 1
            itr += 1
        elif "sidebar-topic" in request.form:
            itr = int(request.form.get('sidebar-topic'))
        elif "home" in request.form:
            return redirect(url_for('main.courses'))
        elif request.form.get("code_filesystem"):
            path = f"file:///{course_dir}/{toc_items[itr]['title']}".replace("\\", "/")
            webbrowser.open(path)

    '''
    GET request, this is used to refresh the webpage if required    
    '''
    last_visited_course = course_dir.split(os.path.sep)[-1]
    commit_current_course_details(
        username=current_user.username,
        last_visited_course=last_visited_course,
        last_visited_topic=toc_items[itr]['title'],
        last_visited_index=itr
    )

    template_folder = "/".join(course_dir[len(root_course_dir) + 1:].split(os.path.sep))
    webpage = f"{template_folder}/{toc_items[itr]['title']}/{toc_items[itr]['title']}.html"
    is_code_present = check_code_present(course_dir, toc_items[itr]['title'])
    rendered_html = render_template(
        "topics_toc.html",
        code_present=is_code_present,
        webpage=webpage,
        folder=f"{toc_items[itr]['title']}",
        toc_items=toc_items,
        itr=itr,
        prev_topic=prev_topic,
        next_topic=next_topic
    )
    return rendered_html


'''
Endpoint to load the code/quiz files in monaco editor
'''
@main.route("/courses/code/<codes>", methods=['GET', 'POST'])
@login_required
def codes(codes):
    current_path_details = get_current_path_details(current_user.username)
    course_dir = current_path_details.last_visited_directory
    directory_path = os.path.join(course_dir, codes)
    encoded_path = base64.b64encode(directory_path.encode()).decode()
    return render_template("monaco-editor.html", encoded_path=encoded_path)


'''
Endpoint to list all the files in monaco-sidebar
'''
@main.route('/courses/list-files')
@login_required
def list_files():
    encoded_path = request.args.get('encoded_path')
    directory_path = base64.b64decode(encoded_path.encode()).decode()
    files = build_folder_structure_for_monaco_sidebar(directory_path, directory_path)
    return jsonify(files)


'''
Endpoint to load file-content in monaco-editor
'''
@main.route('/courses/file-content/<path:filename>')
@login_required
def file_content(filename):
    encoded_path = request.args.get('encoded_path')
    directory_path = base64.b64decode(encoded_path.encode()).decode()
    filename = base64.b64decode(filename.encode()).decode()
    file_path = os.path.join(directory_path, filename)
    return send_file(file_path)


'''
Endpoint to download the folder as zip
'''
@main.route('/courses/download/<folder>', methods=['POST', 'GET'])
@login_required
def download(folder):
    course_dir = root_course_dir
    current_path_details = get_current_path_details(current_user.username)
    if current_path_details is not None:
        course_dir = current_path_details.last_visited_directory
        
    if request.method == "POST":
        if not current_user.downloadaccess:
            return render_template("downloadaccess.html")
        '''
        Copy the course directory to temp folder and zip it
        '''
        temp_folder_path = os.path.join(OS_ROOT, "temp", current_user.username, folder)
        delete_dir(temp_folder_path)
        create_dir(temp_folder_path)
        temp_folder_course_dir = os.path.join(temp_folder_path, folder)
        shutil.copytree(course_dir, temp_folder_course_dir)
        shutil.make_archive(temp_folder_course_dir, 'zip', temp_folder_course_dir)
        return redirect(url_for('main.courses') + f"/tmp/{folder}/{folder}.zip")
    return redirect(url_for('main.courses'))


@main.route("/courses/tmp/<path:filepath>", methods=['POST', 'GET'])
@login_required
def file_download(filepath):
    temp_folder_path = os.path.join(OS_ROOT, "temp", current_user.username)
    try:
        return send_from_directory(temp_folder_path, filepath, as_attachment=True)
    except:
        return render_template("404.html", message="File does not exist")
    

@main.route("/courses/getdownloadaccess", methods=['POST', 'GET'])
@login_required
def getdownloadacess():
    current_user_details = get_current_user_details(current_user.username)
    message = ''
    if request.method == "POST":
        downloadtoken = request.form.get('downloadtoken')
        if downloadtoken == os.getenv('downloadtoken', ''):
            current_user_details.downloadaccess = True
            commit_current_user_details(current_user_details)
            return redirect(url_for('main.courses'))
        else:
            message = 'Please enter correct Download Token and try again.'
    return render_template("downloadaccess.html", message=message)
    
# //////////////////////////////////////////////////////////////////////////////
from .ai_utility import query_gemini

@main.route('/api/chat', methods=['POST'])
@login_required
def post_message():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid input"}), 400

    user_message = ChatMessage(
        user_id=current_user.id,
        username=current_user.username,
        message=data['message'],
        role='user'
    )
    print(data['message'] , "============================================");
    try:
        db.session.add(user_message)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"error": f"Failed to save message: {str(e)}"}, 500

    db.session.add(user_message)
    db.session.commit()

    # Call Gemini API for AI response
    try:
        gemini_response = query_gemini(data['message'])
        print(gemini_response , "gemini response")
        ai_message_content = gemini_response.text 
    except Exception as e:
        ai_message_content = "Sorry, I'm unable to respond right now."

    ai_message = ChatMessage(
        user_id=current_user.id,
        username="Gemini",
        message=ai_message_content,
        role='ai'
    )
    db.session.add(ai_message)
    db.session.commit()

    return jsonify({
        "user_message": data['message'],
        "ai_response": ai_message_content
    })



@main.route('/api/chat/history', methods=['GET'])
@login_required
def get_chat_messages():
    try:
        messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.timestamp).all()

        serialized_messages = [
            {
                "role": "user" if message.role == "user" else "ai",
                "message": message.message,
                "timestamp": message.timestamp.isoformat()
            }
            for message in messages
        ]

        return jsonify(serialized_messages), 200

    except Exception as e:
        print(f"Error fetching chat messages: {e}")
        return jsonify({"error": "Failed to fetch chat messages"}), 500

@main.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', message="Page does not exist"), 404



