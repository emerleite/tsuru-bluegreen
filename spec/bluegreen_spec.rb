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
end
