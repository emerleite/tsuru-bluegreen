require 'spec_helper'

describe BlueGreen do
  let :config do
    {
      'hooks' => {'before_pre'  => 'echo test', 'after_swap'  => 'undefined_command'},
      'newrelic' => {'api_key'  => 'some-api-key', 'app_id'  => '123'},
      'webhook' => {'endpoint' => 'http://example.com', 'payload_extras' => 'key1=value1&key2=value2'}
    }
  end

  let :target do
    "http://tsuru.globoi.com/1.0/"
  end

  let :token do
    "token"
  end

  let :headers do
    {"Content-Type" => "application/json", "Authorization" => "bearer #{token}"}
  end

  subject do
    BlueGreen.new token, target, config
  end

  describe "#get_cname" do
    it "should return a list when present" do
      stub_request(:get, "#{target}apps/xpto")
        .with(headers: headers)
        .to_return(body: '{"cname":["cname1", "cname2"]}')
      expect(subject.get_cname("xpto")).to eql ["cname1", "cname2"]
    end

    it "should return nil when cname list is empty" do
      stub_request(:get, "#{target}apps/xpto")
        .with(headers: headers)
        .to_return(body: '{"cname":[]}')
      expect(subject.get_cname("xpto")).to be_nil
    end
  end

  describe "#remove_cname" do
    let :cnames do
      {"cname" => ["cname1", "cname2"]}
    end

    it "should return true when can remove" do
      stub_request(:delete, "#{target}apps/xpto/cname")
        .with(body: cnames.to_json, headers: headers)
        .to_return(status: 200, body: "")
      expect(subject.remove_cname("xpto", ["cname1", "cname2"])).to be_truthy
    end

    it "should return false when can't remove" do
      stub_request(:delete, "#{target}apps/xpto/cname")
        .with(body: cnames.to_json, headers: headers)
        .to_return(status: 500, body: "")
      expect(subject.remove_cname("xpto", ["cname1", "cname2"])).to be_falsy
    end
  end

  describe "#set_cname" do
    let :cnames do
      {"cname" => ["cname1", "cname2"]}
    end

    it "should return true when can remove" do
      stub_request(:post, "#{target}apps/xpto/cname")
        .with(body: cnames.to_json, headers: headers)
        .to_return(status: 200, body: "")
      expect(subject.set_cname("xpto", ["cname1", "cname2"])).to be_truthy
    end

    it "should return false when can't remove" do
      stub_request(:post, "#{target}apps/xpto/cname")
        .with(body: cnames.to_json, headers: headers)
        .to_return(status: 500, body: "")
      expect(subject.set_cname("xpto", ["cname1", "cname2"])).to be_falsy
    end
  end

  describe "#env_set" do
    let :data do
      {"TAG" => "tag_value"}
    end

    it "should return true when can remove" do
      stub_request(:post, "#{target}apps/xpto/env?noRestart=true")
        .with(body: data.to_json, headers: headers)
        .to_return(status: 200, body: "")
      expect(subject.env_set("xpto", "TAG", "tag_value")).to be_truthy
    end

    it "should return false when can't remove" do
      stub_request(:post, "#{target}apps/xpto/env?noRestart=true")
        .with(body: data.to_json, headers: headers)
        .to_return(status: 500, body: "")
      expect(subject.env_set("xpto", "TAG", "tag_value")).to be_falsy
    end
  end

  describe "#env_get" do
    let :data do
      ["TAG"]
    end

    it "returns a value when present" do
      stub_request(:get, "#{target}apps/xpto/env")
        .with(body: data.to_json, headers: headers)
        .to_return(body: '[{"name":"TAG", "public":true, "value":"1.0"}]')
      expect(subject.env_get("xpto", "TAG")).to eql "1.0"
    end

    it "returns nil for null values" do
      stub_request(:get, "#{target}apps/xpto/env")
        .with(body: data.to_json, headers: headers)
        .to_return(body: "null")
      expect(subject.env_get("xpto", "TAG")).to be_nil
    end

    it "returns nil for env without matching value" do
      stub_request(:get, "#{target}apps/xpto/env")
        .with(body: data.to_json, headers: headers)
        .to_return(body: "[]")
      expect(subject.env_get("xpto", "TAG")).to be_nil
    end
  end

  describe "#total_units" do
    it "returns a empty hash when units is empty" do
      stub_request(:get, "#{target}apps/xpto")
        .with(headers: headers)
        .to_return(body: '{"units":[]}')
      expect(subject.total_units("xpto")).to eql({})
    end

    it "returns units grouped per process name" do
      stub_request(:get, "#{target}apps/xpto")
        .with(headers: headers)
        .to_return(body: '{"units":[{"ProcessName": "web"}, {"ProcessName": "resque"}, {"ProcessName": "web"}]}')

      expect(subject.total_units("xpto")).to eql({"web" => 2, "resque" => 1})
    end
  end

  describe "#remove_units" do
    let(:url) { "#{target}apps/xpto/units"}
    let(:headers_form) { headers.merge({"Content-Type" => "application/x-www-form-urlencoded"})}

    it "returns true when removes web units" do
      stub_request(:delete, url)
        .with(query: {units: 2, process: :web}, headers: headers_form)
        .to_return(status: 200, body: "")

      allow(subject).to receive(:total_units).and_return({'web' => 2})
      expect(subject.remove_units("xpto")).to eql(true)
    end

    it "returns true when removes web and resque units" do
      stub_request(:delete, url)
        .with(query: {units: 2, process: :web}, headers: headers_form)
        .to_return(status: 200, body: "")
      stub_request(:delete, url)
        .with(query: {units: 1, process: :resque}, headers: headers_form)
        .to_return(status: 200, body: "")

      allow(subject).to receive(:total_units).and_return({'web' => 2, 'resque' => 1})
      expect(subject.remove_units("xpto")).to eql(true)
    end

    it "allows keep units" do
      stub_request(:delete, url)
        .with(query: {units: 3, process: :web}, headers: headers_form)
        .to_return(status: 200, body: "")
      stub_request(:delete, url)
        .with(query: {units: 1, process: :resque}, headers: headers_form)
        .to_return(status: 200, body: "")

      allow(subject).to receive(:total_units).and_return({'web' => 4, 'resque' => 2})
      expect(subject.remove_units("xpto", 1)).to be_truthy
    end

    it 'returns false when doesnt remove all process types' do
      stub_request(:delete, url)
        .with(query: {units: 2, process: :web}, headers: headers_form)
        .to_return(status: 200, body: "")
      stub_request(:delete, url)
        .with(query: {units: 1, process: :resque}, headers: headers_form)
        .to_return(status: 500, body: "")

      allow(subject).to receive(:total_units).and_return({'web' => 2, 'resque' => 1})
      expect(subject.remove_units("xpto")).to be_falsy
    end
  end

  describe "#add_units" do
    let(:url) { "#{target}apps/xpto/units"}

    it "returns true when adds web units" do
      stub_request(:put, url)
        .with(query: {units: 1, process: :web}, headers: headers)
        .to_return(status: 200, body: "")

      allow(subject).to receive(:total_units).and_return({'web' => 1}, {'web' => 2})
      expect(subject.add_units("xpto", {'web' =>  2})).to eql(true)
    end

    it "returns true when adds web and resque units" do
      stub_request(:put, url)
        .with(query: {units: 3, process: :web}, headers: headers)
        .to_return(status: 200, body: "")
      stub_request(:put, url)
        .with(query: {units: 1, process: :resque}, headers: headers)
        .to_return(status: 200, body: "")

      allow(subject).to receive(:total_units).and_return({'web' => 2, 'resque' => 1}, {'web' => 5, 'resque' => 1}, {'web' => 5, 'resque' => 2})
      expect(subject.add_units("xpto", {'web' =>  5, 'resque' => 2})).to eql(true)
    end

    it "returns true when adds only web units" do
      stub_request(:put, url)
        .with(query: {units: 3, process: :web}, headers: headers)
        .to_return(status: 200, body: "")

      allow(subject).to receive(:total_units).and_return({'web' => 2, 'resque' => 1}, {'web' => 5, 'resque' => 1})
      expect(subject.add_units("xpto", {'web' => 5, 'resque' => 1})).to eql(true)
    end

    it "returns false when doesnt add units" do
      stub_request(:put, url)
        .with(query: {units: 1, process: :web}, headers: headers)
        .to_return(status: 500, body: "")

      allow(subject).to receive(:total_units).and_return({'web' => 2}, {'web' => 3})
      expect(subject.add_units("xpto", {'web' => 3})).to be_falsy
    end

    it "returns false when doesnt add units all process" do
      stub_request(:put, url)
        .with(query: {units: 1, process: :web}, headers: headers)
        .to_return(status: 500, body: "")
      stub_request(:put, url)
        .with(query: {units: 1, process: :resque}, headers: headers)
        .to_return(status: 200, body: "")

      allow(subject).to receive(:total_units).and_return({'web' => 2, 'resque' => 1}, {'web' => 2, 'resque' => 2})
      expect(subject.add_units("xpto", {'web' => 3, 'resque' => 2})).to be_falsy
    end
  end

  describe "#notify_newrelic" do
    let(:url) { "http://api.newrelic.com/deployments.xml"}
    let(:api_key) { 'some-api-key' }
    let(:headers_newrelic) { {"Content-Type" =>  "application/x-www-form-urlencoded", "x-api-key" =>  api_key}}


    it "notifies newrelic when config defined" do
      stub_request(:post, url)
        .with(body:  {"deployment"=>{"application_id"=>"123", "revision"=>"1.0"}}, headers: headers.merge(headers_newrelic))
        .to_return(status: 200, body: "")

      expect(subject.notify_newrelic('1.0')).to be_truthy
    end

    it "doesnt notifies newrelic when config is not defined" do
      subject.instance_variable_set("@newrelic", {})
      expect(subject.notify_newrelic('1.0')).to be_falsy
    end

    it "doesnt notifies newrelic when wrong api key" do
      stub_request(:post, url)
        .with(body:  {"deployment"=>{"application_id"=>"123", "revision"=>"1.0"}}, headers: headers.merge(headers_newrelic))
        .to_return(status: 403, body: "")

      expect(subject.notify_newrelic('1.0')).to be_falsy
    end

    it "doesnt notifies newrelic when error" do
      stub_request(:post, url)
        .with(body:  {"deployment"=>{"application_id"=>"123", "revision"=>"1.0"}}, headers: headers.merge(headers_newrelic))
        .to_return(status: 500, body: "")

      expect(subject.notify_newrelic('1.0')).to be_falsy
    end
  end

  describe "#run_webhook" do
    let(:url) { "http://example.com"}
    let(:payload) { 'key1=value1&key2=value2' }
    let(:headers_webhook) { {"Content-Type" =>  "application/x-www-form-urlencoded"} }


    it "runs webhook when config defined" do
      stub_request(:post, url)
        .with(body:  {"key1"=>"value1", "key2"=>"value2", "tag" => "1.0"}, headers: headers.merge(headers_webhook))
        .to_return(status: 200, body: "")

      expect(subject.run_webhook('1.0')).to be_truthy
    end

    it "doesnt run webhook when config is not defined" do
      subject.instance_variable_set("@webhook", {})
      expect(subject.run_webhook('1.0')).to be_falsy
    end

    it "doesnt run webhook when error" do
      stub_request(:post, url)
        .with(body:  {"key1"=>"value1", "key2"=>"value2", "tag" => "1.0"}, headers: headers.merge(headers_webhook))
        .to_return(status: 500, body: "")

      expect(subject.run_webhook('1.0')).to be_falsy
    end
  end

  describe '#run_command' do
    it 'returns true on success' do
      expect(subject.run_command('echo test')).to be_truthy
    end

    it 'returns false on error' do
      expect(subject.run_command('cat undefined_file')).to be_falsy
    end

    it 'accepts enviroment variable' do
      expect(subject.run_command('./test/env_test.sh', {'VAR' => '0'})).to be_truthy
      expect(subject.run_command('./test/env_test.sh', {'VAR' => '1'})).to be_falsy
    end
  end

  describe "#request" do
    let(:headers_form) { headers.merge({"Content-Type" => "application/x-www-form-urlencoded"})}
    it 'makes a http request' do
      url =  'http://example.com?units=1'
      stub_request(:put, url)
        .with(query: {units: 1}, headers: headers.merge(headers_form))
        .to_return(status: 200, body: "{}")

      expect(subject.send(:request, :put, url, {headers: headers_form}))
    end
  end
end
