FROM ruby:3.3.6-slim

RUN apt-get update && \
    apt-get install -y build-essential libmysqlclient-dev git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone --recursive https://github.com/seven1m/bible_api.git /app

RUN gem install bundler && bundle install

EXPOSE 4567

CMD ["bundle", "exec", "ruby", "app.rb", "-o", "0.0.0.0", "-p", "4567"]
